import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

async def fetch_case_data(case_type: str, case_number: str, case_year: str):
    """
    Final version with correct extraction patterns for Delhi High Court
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            print("🔍 Navigating to Delhi High Court...")
            await page.goto("https://delhihighcourt.nic.in/", timeout=60000)
            
            # Click Case Status
            try:
                await page.click("text=Case Status", timeout=5000)
                print("✅ Clicked Case Status link")
            except:
                await page.goto("https://delhihighcourt.nic.in/app/get-case-type-status")
            
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)
            
            print("🔍 Filling form...")
            
            # Fill case type dropdown (skip language dropdown)
            selects = await page.locator('select').all()
            for i, select in enumerate(selects):
                try:
                    current_value = await select.input_value()
                    if current_value != 'Hindi':  # Skip language dropdown
                        await select.select_option(value=case_type)
                        print(f"✅ Set case type to: {case_type}")
                        break
                except:
                    continue
            
            # Fill case number
            await page.fill('input[name="case_number"]', case_number)
            print(f"✅ Filled case number: {case_number}")
            
            # Fill case year (look for year field)
            inputs = await page.locator('input[type="text"]').all()
            for input_elem in inputs:
                try:
                    placeholder = await input_elem.get_attribute('placeholder') or ""
                    name = await input_elem.get_attribute('name') or ""
                    if 'year' in placeholder.lower() or 'year' in name.lower():
                        await input_elem.fill(case_year)
                        print(f"✅ Filled case year: {case_year}")
                        break
                except:
                    continue
            
            print("\n🔴 COMPLETE THESE STEPS MANUALLY:")
            print("1. Solve the CAPTCHA")
            print("2. Click SUBMIT button") 
            print("3. Wait for results")
            print("\nScript will auto-detect results...")
            
            # Wait for results with the pattern we know works
            try:
                await page.wait_for_function(f"""
                    () => {{
                        const text = document.body.innerText;
                        return text.includes('{case_number}') && 
                               (text.includes('SEEMA RANI') || text.includes('Petitioner') || text.includes('VS'));
                    }}
                """, timeout=600000)
                print("✅ Results detected!")
            except:
                print("⏰ Proceeding with extraction...")
            
            await asyncio.sleep(2)
            
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text()
            
            print("🔍 Extracting with specialized Delhi High Court patterns...")
            
            case_details = {}
            
            # **CORRECTED EXTRACTION PATTERNS** based on your actual output
            
            # Pattern 1: Extract from the table structure we saw in your output
            # Looking for: SEEMA RANI & ORS.VS.    MUNICIPAL CORPORATION OF DELHI
            pattern1 = rf'{re.escape(case_type)}\s*-\s*{re.escape(case_number)}\s*/\s*{re.escape(case_year)}.*?\[.*?\].*?Orders([A-Z][A-Z\s&.,()]+?)VS\.?\s+([A-Z][A-Z\s&.,()]+?)(?:NEXT DATE|Last Date|\n)'
            match1 = re.search(pattern1, page_text, re.IGNORECASE | re.DOTALL)
            
            if match1:
                petitioner = match1.group(1).strip()
                respondent = match1.group(2).strip()
                case_details['petitioner'] = petitioner
                case_details['respondent'] = respondent
                print(f"✅ Pattern 1 - Petitioner: {petitioner}")
                print(f"✅ Pattern 1 - Respondent: {respondent}")
            
            # Pattern 2: Table-based extraction
            if not case_details.get('petitioner'):
                # Look for table rows containing our case
                table_pattern = rf'({re.escape(case_number)}.*?{re.escape(case_year)}.*?)(?:Showing|\n\n)'
                table_match = re.search(table_pattern, page_text, re.DOTALL)
                
                if table_match:
                    table_content = table_match.group(1)
                    # Extract petitioner vs respondent from table content
                    vs_pattern = r'([A-Z][A-Z\s&.,()]+?)\s*VS\.?\s*([A-Z][A-Z\s&.,()]+?)(?:\s*NEXT DATE|\s*Last Date|\s*COURT)'
                    vs_match = re.search(vs_pattern, table_content, re.IGNORECASE)
                    
                    if vs_match:
                        petitioner = vs_match.group(1).strip()
                        respondent = vs_match.group(2).strip()
                        case_details['petitioner'] = petitioner
                        case_details['respondent'] = respondent
                        print(f"✅ Pattern 2 - Petitioner: {petitioner}")
                        print(f"✅ Pattern 2 - Respondent: {respondent}")
            
            # Pattern 3: Direct text extraction from your exact output format
            if not case_details.get('petitioner'):
                # Based on your output: "SEEMA RANI & ORS.VS.    MUNICIPAL CORPORATION OF DELHI"
                direct_pattern = r'([A-Z][A-Z\s&.,()]+?)VS\.?\s+([A-Z][A-Z\s&.,()]+?)(?:\s*NEXT DATE)'
                direct_match = re.search(direct_pattern, page_text)
                
                if direct_match:
                    petitioner = direct_match.group(1).strip()
                    respondent = direct_match.group(2).strip()
                    case_details['petitioner'] = petitioner
                    case_details['respondent'] = respondent
                    print(f"✅ Pattern 3 - Petitioner: {petitioner}")
                    print(f"✅ Pattern 3 - Respondent: {respondent}")
            
            # Extract additional information
            # Case status
            status_match = re.search(rf'{re.escape(case_number)}.*?\[(.*?)\]', page_text)
            if status_match:
                case_details['case_status'] = status_match.group(1).strip()
                print(f"✅ Case Status: {case_details['case_status']}")
            
            # Last date
            last_date_match = re.search(r'Last Date:\s*(\d{2}/\d{2}/\d{4})', page_text)
            if last_date_match:
                case_details['last_hearing_date'] = last_date_match.group(1)
                print(f"✅ Last Hearing Date: {case_details['last_hearing_date']}")
            
            # Court number
            court_match = re.search(r'COURT NO:\s*(\d+)', page_text)
            if court_match:
                case_details['court_number'] = court_match.group(1)
                print(f"✅ Court Number: {case_details['court_number']}")
            
            # Next date
            if 'NEXT DATE: NA' in page_text:
                case_details['next_hearing_date'] = "Case disposed - no next date"
            else:
                next_date_match = re.search(r'NEXT DATE:\s*(\d{2}/\d{2}/\d{4})', page_text)
                if next_date_match:
                    case_details['next_hearing_date'] = next_date_match.group(1)
                else:
                    case_details['next_hearing_date'] = "Check latest orders for next date"
            
            # Set filing date
            case_details['filing_date'] = "Not displayed on results page"
            
            # Look for orders link
            orders = []
            if 'Orders' in page_text:
                orders.append({
                    'description': 'Case Orders (click Orders link on results page)',
                    'pdf_link': 'Available on court website',
                    'date': case_details.get('last_hearing_date', 'Check court records')
                })
            case_details['orders'] = orders
            
            # Final validation and cleanup
            if case_details.get('petitioner'):
                # Clean up common extraction artifacts
                petitioner = case_details['petitioner']
                petitioner = re.sub(r'\s+', ' ', petitioner).strip()
                # Remove common trailing artifacts
                petitioner = re.sub(r'\s*(Orders|VS|Vs|vs)\s*$', '', petitioner).strip()
                case_details['petitioner'] = petitioner
            
            if case_details.get('respondent'):
                respondent = case_details['respondent'] 
                respondent = re.sub(r'\s+', ' ', respondent).strip()
                # Remove trailing artifacts
                respondent = re.sub(r'\s*(NEXT DATE|Last Date|COURT).*$', '', respondent).strip()
                case_details['respondent'] = respondent
            
            print("\n📋 FINAL EXTRACTION RESULTS:")
            print(f"   Petitioner: {case_details.get('petitioner', 'Not extracted')}")
            print(f"   Respondent: {case_details.get('respondent', 'Not extracted')}")
            print(f"   Status: {case_details.get('case_status', 'Not found')}")
            print(f"   Last Date: {case_details.get('last_hearing_date', 'Not found')}")
            print(f"   Court: {case_details.get('court_number', 'Not found')}")
            
            await asyncio.sleep(10)
            await browser.close()
            
            if case_details.get('petitioner') and case_details.get('respondent'):
                return {"data": case_details, "raw_html": html_content, "error": None}
            else:
                return {
                    "data": case_details, 
                    "raw_html": html_content, 
                    "error": "Could not extract petitioner/respondent names despite finding case data"
                }
            
        except Exception as e:
            await browser.close()
            return {"data": None, "raw_html": None, "error": str(e)}

if __name__ == '__main__':
    test_case_type = "W.P.(C)"
    test_case_number = "11199" 
    test_case_year = "2025"
    
    print("🚀 FINAL CORRECTED Delhi High Court Scraper")
    print("=" * 60)
    print("🎯 This version is specifically tuned for the exact data format")
    print("   we saw in your previous successful run!")
    print("=" * 60)
    
    result = asyncio.run(fetch_case_data(test_case_type, test_case_number, test_case_year))
    
    print("\n🏆 FINAL RESULTS:")
    print("=" * 50)
    
    if result['data']:
        print("✅ SUCCESSFULLY EXTRACTED CASE DATA:")
        print(json.dumps(result['data'], indent=2, ensure_ascii=False))
        
        data = result['data']
        if data.get('petitioner') and data.get('respondent'):
            print(f"\n🎉 PERFECT! Successfully extracted:")
            print(f"   📋 Case: {test_case_type} {test_case_number}/{test_case_year}")
            print(f"   👤 Petitioner: {data['petitioner']}")
            print(f"   🏢 Respondent: {data['respondent']}")
            print(f"   ⚖️  Status: {data.get('case_status', 'Unknown')}")
            print(f"   📅 Last Hearing: {data.get('last_hearing_date', 'Unknown')}")
        else:
            print("⚠️  Partial extraction - some data may be missing")
    
    if result['error']:
        print(f"❌ Error: {result['error']}")
