from playwright.sync_api import sync_playwright
import datetime
import time
import config
import sys
from io import BytesIO
from PIL import Image
import re

def parse_time(time_str):
    try:
        # Expected formats: "10:00 AM", "1:00 PM"
        return datetime.datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except ValueError:
        return None

def scrape_schedule(url):
    print(f"Launching browser to scrape {url}...")
    slots = []
    
    with sync_playwright() as p:
        # Try finding chromium, fallback to others if needed
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Set viewport large enough to see the whole grid
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            print("Navigating...")
            # Relaxing wait condition
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"Page loaded. Title: {page.title()}")
            
            # Wait a bit for JS to kick in
            time.sleep(5)
            
            # Take initial screenshot
            page.screenshot(path="debug_initial_load.png")
            
            # Check for "Block Download" or other text
            if "permission" in page.content().lower():
                print("Page contains 'permission' related text.")

            # Wait for any iframe first
            print("Waiting for any iframe...")
            page.wait_for_selector("iframe", timeout=30000)
            
            # Try to find the specific Excel frame
            frame_element = page.query_selector("iframe[id*='WacFrame_Excel']")
            if not frame_element:
                 # Fallback: looks for the biggest iframe?
                 print("Specific WacFrame not found, checking all iframes...")
                 iframes = page.query_selector_all("iframe")
                 for i, f in enumerate(iframes):
                     print(f"Iframe {i}: {f.get_attribute('id')} {f.get_attribute('src')}")
                     if "sourcedoc" in (f.get_attribute('src') or ""):
                         frame_element = f
                         break
            
            if not frame_element:
                print("Could not find Excel content frame.")
                page.screenshot(path="debug_no_frame.png")
                return []
                
            frame = frame_element.content_frame()
            if not frame:
                 print("Found iframe element but no content frame.")
                 return []
            
            print("Frame found. Waiting for grid content...")
            try:
                # Wait for any text editor box to appear
                frame.wait_for_selector(".ql-editor", timeout=60000)
            except Exception:
                print("Timed out waiting for '.ql-editor'. taking screenshot.")
                page.screenshot(path="debug_timeout.png")
                # Dump frame content
                with open("debug_frame.html", "w") as f:
                    f.write(frame.content())
                return []
                print("Timed out waiting for 'MONDAY'. taking screenshot.")
                page.screenshot(path="debug_timeout.png")
                # Dump frame content
                with open("debug_frame.html", "w") as f:
                    f.write(frame.content())
                return []
            
            # Now we need to efficiently find slots.
            # Strategy:
            # 1. Find all elements containing "PHYS 2002" (or "PHYS" generally if we want to filter later)
            # 2. For each, check background color.
            # 3. For each valid one, determine Column (Day) and Row (Time).
            
            # Get data cells that might contain our text
            # We use a broad selector because exact class names change. 
            # We look for text nodes? No, elements.
            
            # Scroll to ensure rendering (Excel Online is virtualized)
            # Try scrolling the grid container
            try:
                # focus grid
                frame.click(".ewa-grid-container")
                frame.keyboard.press("PageDown")
                time.sleep(2)
                frame.keyboard.press("PageUp")
                time.sleep(2)
            except:
                pass

            # Let's find all text elements matching "PHYS" first
            # "PHYS" might be split across spans.
            # Try finding by selector specific to grid cells
            potential_cells = frame.locator(".ewa-grid-cell").all()
            print(f"Found {len(potential_cells)} total grid cells in DOM.")
            
            phys_cells = []
            for cell in potential_cells:
                txt = cell.text_content()
                if "PHYS" in txt:
                    print(f"Found PHYS cell: '{txt}'")
                    phys_cells.append(cell)
            
            print(f"Found {len(phys_cells)} cells containing 'PHYS' after filtering.")
            
            # Map headers for coordinates
            
            # Map headers for coordinates
            # We need bounding boxes of headers
            days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
            day_columns = {} # { 'MONDAY': {left: x, right: y}, ... }
            
            for day in days:
                el = frame.get_by_text(day, exact=True).first
                if el.is_visible():
                    box = el.bounding_box()
                    if box:
                        day_columns[day] = box
                        # print(f"Header {day}: {box}")

            # Map time rows
            # We'll search for time strings "10:00 AM", etc.
            # This relies on them being visible.
            times = {} # { time_obj: {top: y, bottom: y} }
            # Heuristic list of times
            start_hour = 8
            end_hour = 18
            for h in range(start_hour, end_hour + 1):
                for m in [0, 30]:
                    dt = datetime.datetime(2000, 1, 1, h, m)
                    t_str = dt.strftime("%-I:%M %p") # 10:00 AM
                    if t_str.startswith("0"): t_str = t_str[1:] # Strip leading 0 if needed specific format?
                    
                    # Try simplified formats
                    t_str_simple = f"{h if h <= 12 else h-12}:{m:02d} {'AM' if h < 12 else 'PM'}"
                    
                    # Find element
                    # Note: Excel online might render "10:00 AM" in a specific header cell
                    # We utilize the fact that row headers are usually on the left.
                    # Let's try to match text exactly.
                    el = frame.get_by_text(t_str_simple, exact=True).first
                    if el.count() > 0 and el.is_visible():
                         box = el.bounding_box()
                         if box:
                             times[dt.time()] = box
                             # print(f"Row {t_str_simple}: {box}")
            
            # Strategy:
            # 1. Find all text containers (ql-editor or broadly)
            # 2. Filter for "PHYS"
            # 3. Screenshot and identify color
            # 4. Parse text for time
            
            # Find floating text boxes
            # In the dump, they are div.ql-editor
            potential_elements = frame.locator(".ql-editor").all()
            print(f"Found {len(potential_elements)} potential text slots.")
            
            # Take screenshot for color analysis
            png_bytes = page.screenshot()
            pil_image = Image.open(BytesIO(png_bytes))
            
            for el in potential_elements:
                try:
                    text = el.text_content()
                    if "PHYS" not in text and "Physics" not in text:
                        continue
                        
                    box = el.bounding_box()
                    if not box:
                        continue
                        
                    # Color check
                    # Sample center of the box
                    cx = box['x'] + box['width'] / 2
                    cy = box['y'] + box['height'] / 2
                    
                    # We need to account for frame offset maybe?
                    # page.screenshot captures viewport.
                    # iframe coordinates are relative to iframe.
                    # If iframe is full page, it matches.
                    # Bounding box is relative to frame.
                    
                    # Let's assume standard layout.
                    # Sample a few points
                    try:
                        # Get pixel from image (coordinate system might need adjustment if iframe is offset)
                        # For now assume top-left match.
                        pixel = pil_image.getpixel((cx, cy))
                        # pixel is (R, G, B, A)
                        r, g, b = pixel[:3]
                        print(f"Checking slot '{text[:20]}...' at ({cx},{cy}) Color: ({r},{g},{b})")
                        
                        is_blue = False
                        # Target: 222, 234, 246 (Light Blue)
                        # Allow tolerance
                        if b > r and b > g and b > 200:
                            is_blue = True
                        if abs(r - 222) < 40 and abs(g - 234) < 40 and abs(b - 246) < 40:
                            is_blue = True
                            
                        # If Blue, parse time
                        if is_blue or "PHYS 2002" in text: # Fallback to text matching if color fails (transparent box)
                             # Extract Day/Time from text
                             # Patterns: "MONDAY 10am-4pm", "1:30-2:30", etc.
                             
                             # Regex for Day
                             found_day = None
                             for d in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]:
                                 if d in text.upper():
                                     found_day = d
                                     break
                             
                             # Regex for Time
                             # Formats: 
                             # 10am-4pm, 10:00-11:30, 1:30-2:30
                             # 11:30 - 1:00
                             
                             # Clean text
                             clean_text = text.replace(u'\xa0', ' ').replace('\n', ' ')
                             
                             # Regex patterns
                             # 1. "10am-4pm" or "10am - 4pm"
                             # 2. "10:00-11:30"
                             # 3. "1:30 - 2:30"
                             
                             time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', clean_text, re.IGNORECASE)
                             print(f"Regex match for '{clean_text[:50]}...': {time_match}")
                             
                             if clean_text.lower().find("10am-4pm") != -1: # Explicit check for the one we found
                                 start_time_str = "10:00 am"
                                 end_time_str = "4:00 pm"
                             elif time_match:
                                 start_time_str = time_match.group(1)
                                 end_time_str = time_match.group(2)
                             else:
                                 start_time_str = None
                                 
                             if start_time_str and found_day:
                                 # Parse time strings
                                 def parse_t(t_str):
                                     t_str = t_str.lower().strip()
                                     if ":" not in t_str:
                                         if "am" in t_str or "pm" in t_str:
                                             t_str = t_str.replace("am", ":00 am").replace("pm", ":00 pm")
                                         else:
                                             # Assume am/pm based on value? 10 -> 10am, 1 -> 1pm?
                                             val = int(re.sub(r'\D', '', t_str))
                                             if val < 8: t_str += ":00 pm"
                                             else: t_str += ":00 am"
                                     
                                     # Add am/pm if missing. 
                                     # If 10:00, usually AM. If 1:00, usually PM.
                                     if "am" not in t_str and "pm" not in t_str:
                                         val = int(re.split(':', t_str)[0])
                                         if val < 8 or val == 12: t_str += " pm"
                                         else: t_str += " am"
                                     
                                     try:
                                         return datetime.datetime.strptime(t_str, "%I:%M %p").time()
                                     except:
                                          # Try without space
                                          try:
                                              return datetime.datetime.strptime(t_str.replace(" ", ""), "%I:%M%p").time()
                                          except:
                                              return None

                                 start_t = parse_t(start_time_str)
                                 end_t = parse_t(end_time_str)
                                 
                                 if start_t and end_t:
                                     day_map_idx = {"MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2, "THURSDAY": 3, "FRIDAY": 4}[found_day]
                                     today = datetime.date.today()
                                     current_weekday = today.weekday()
                                     days_diff = day_map_idx - current_weekday
                                     if days_diff < 0: days_diff += 7 # Next week if passed? Or assume current week if Monday?
                                     
                                     # If running on Monday, and slot is Monday, diff=0. Correct.
                                     # If running on Tuesday, and slot is Monday, diff=-1 -> +6 = Next Monday.
                                     
                                     slot_date = today + datetime.timedelta(days=days_diff)
                                     start_dt = datetime.datetime.combine(slot_date, start_t)
                                     end_dt = datetime.datetime.combine(slot_date, end_t)
                                     
                                     # Handle titles
                                     title_clean = re.sub(r'\s+', ' ', text).strip()
                                     
                                     slots.append({
                                         'start': start_dt,
                                         'end': end_dt,
                                         'title': f"PHYS2002: {title_clean[:30]}..."
                                     })
                                     print(f"  -> Added slot: {start_dt} - {end_dt}")
                                 
                    except Exception as e:
                        print(f"Color check failed: {e}")

                except Exception as e:
                    print(f"Element error: {e}")


        except Exception as e:
            print(f"Scraping error: {e}")
            page.screenshot(path="debug_error.png")
            with open("debug_error.html", "w") as f:
                f.write(page.content())
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
            
    return slots

if __name__ == "__main__":
    # Test run
    print(scrape_schedule(config.SCHEDULE_URL))
