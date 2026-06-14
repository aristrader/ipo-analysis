# Audit of 88 Unresolved Price Mismatches

This document records the manual audit performed on the 88 stocks that had >20% price discrepancy between Chittorgarh's listing open price and our earliest Bhavcopy record.

## Category 1: Genuinely Missing Corporate Actions
These companies had deeply obscure stock splits or bonuses that were missing from both the NSE API and Yahoo Finance.

| ISIN | Company | Chittorgarh Open | Bhavcopy Open | Diff % | Identified Corporate Action (To be manually overridden) |
| --- | --- | --- | --- | --- | --- |
| INE778I01024 | Aishwarya Telecom Ltd. | 50.1 | 4.43 | 91.2% | 2:1 Split (Feb 2010) |
| INE671T01028 | Darshan Orna Ltd. | 60.8 | 6.7 | 89.0% | 5:1 Split, 11:10 Bonus |
| INE757T01025 | Artemis Electricals Ltd. | 70.0 | 13.85 | 80.2% | 10:1 Split, Multiple Bonuses |
| INE0KY201021 | Maagh Advertising & Marketing Services Ltd. | 62.3 | 13.85 | 77.8% | 10:1 Split, 1:4 Bonus |
| INE191O01010 | Lakhotia Polyesters (India) Ltd. | 35.8 | 8.0 | 77.7% | 18:10 Bonus |
| INE669Y01022 | Sharika Enterprises Ltd. | 51.6 | 11.5 | 77.7% | 2:1 Split, 1:1 Bonus |
| INE399K01017 | Indiabulls Power Ltd. | 44.95 | 11.4 | 74.6% | Bonus issue reported |
| INE0E4I01027 | Ascensive Educare Ltd. | 27.6 | 8.2 | 70.3% | 10:1 Split (Feb 2025) |
| INE899O01018 | Edynamics Solutions Ltd. | 25.4 | 7.8 | 69.3% | 2:1 Bonus (Dec 2011) |
| INE279P01036 | Satkar Finlease Ltd. | 19.9 | 6.13 | 69.2% | 10:1 Split (Dec 2016) |
| INE849M01017 | Tarini International Ltd. | 42.0 | 14.0 | 66.7% | 1:1 and 1:10 Bonus |
| INE442V01012 | Prime Customer Services Ltd. | 169.0 | 60.1 | 64.4% | 2:1 Bonus (May 2021) |
| INE413X01035 | 7NR Retail Ltd. | 27.0 | 10.17 | 62.3% | 1:10 Reverse Split, 10:1 Split, 1:5 Bonus |
| INE01A501027 | Ranjeet Mechatronics Ltd. | 27.5 | 12.49 | 54.6% | 2:1 Split, 1:1 Bonus (Apr 2025) |
| INE700V01021 | Shashijit Infraprojects Ltd. | 15.85 | 7.54 | 52.4% | 5:1 Split, 1:5 Bonus |
| INE541R01019 | Filtra Consultants & Engineers Ltd. | 42.8 | 21.1 | 50.7% | Multiple Bonuses (1:3, 1:5, 3:2) |
| INE00TV01023 | Sudarshan Pharma Industries Ltd. | 73.0 | 42.15 | 42.3% | 10:1 Split (Nov 2024) |
| INE030U01025 | Khemani Distributors & Marketing Ltd. | 105.0 | 60.8 | 42.1% | 2:1 Split, 1:1 Bonus |
| INE552Q01018 | Encash Entertainment Ltd. | 44.0 | 25.85 | 41.2% | 10:1 Split (Mar 2015) |
| INE084Q01012 | Anisha Impex Ltd. | 13.7 | 8.05 | 41.2% | 20:1 Bonus (Nov 2013) |
| INE973X01012 | Poojawestern Metaliks Ltd. | 53.4 | 39.5 | 26.0% | 1:1 Bonus (Jan 2020) |

## Category 2: Market Crashes, Delistings, and Delayed History
The remaining 67 companies had **ZERO** unrecorded stock splits or bonuses. The massive discrepancies are genuine reflections of market wipeouts, scams resulting in 90% crashes, or Bhavcopy history beginning several years post-IPO after the stock had already naturally decayed.

| ISIN | Company | Chittorgarh Open | Bhavcopy Open | Diff % | Audit Status |
| --- | --- | --- | --- | --- | --- |
| INE900K01012 | Aster Silicates Ltd. | 127.7 | 10.7 | 91.6% | Verified No Split / Crash |
| INE274I01016 | Suryachakra Power Corp.Ltd. | 30.0 | 2.65 | 91.2% | Verified No Split / Crash |
| INE253N01010 | Max Alert Systems Ltd. | 51.5 | 5.12 | 90.1% | Verified No Split / Crash |
| INE209L01016 | Commercial Engineers & Body Builders Co.Ltd. | 122.8 | 12.31 | 90.0% | Verified No Split / Crash |
| INE964H01014 | Shriram EPC Ltd. | 290.0 | 29.3 | 89.9% | Verified No Split / Crash |
| INE368I01016 | Niraj Cement Structurals Ltd. | 185.0 | 22.45 | 87.9% | Verified No Split / Crash |
| INE05BN01027 | Cian Healthcare Ltd. | 62.0 | 7.5 | 87.9% | Verified No Split / Crash |
| INE183H01011 | XL Telecom Ltd. | 177.1 | 23.5 | 86.7% | Verified No Split / Crash |
| INE191P01017 | GCM Capital Advisors Ltd. | 33.55 | 4.61 | 86.3% | Verified No Split / Crash |
| INE311H01018 | Mudra Lifestyle Ltd. | 94.8 | 13.15 | 86.1% | Verified No Split / Crash |
| INE596O01010 | Newever Trade Wings Ltd. | 12.2 | 2.05 | 83.2% | Verified No Split / Crash |
| INE422B01016 | Midvalley Entertainment Ltd. | 73.0 | 12.5 | 82.9% | Verified No Split / Crash |
| INE149O01018 | Kavita Fabrics Ltd. | 40.9 | 8.4 | 79.5% | Verified No Split / Crash |
| INE119G01025 | Vijayeswari Textiles Ltd. FPO | 90.05 | 18.85 | 79.1% | Verified No Split (Subagent Hallucination corrected) |
| INE688I01017 | Future Capital Holdings Ltd. | 1044.0 | 222.3 | 78.7% | Verified No Split / Crash |
| INE266H01014 | Sree Sakthi Paper Mills Ltd. | 38.0 | 8.49 | 77.7% | Verified No Split / Crash |
| INE521J01018 | Career Point Infosystems Ltd. | 461.0 | 110.05 | 76.1% | Verified No Split / Crash |
| INE320H01019 | Saamya Biotech (India) Ltd. | 17.5 | 4.2 | 76.0% | Verified No Split / Crash |
| INE218P01018 | Amrapali Capital & Finance Services Ltd. | 100.6 | 25.0 | 75.1% | Verified No Split / Crash |
| INE703H01016 | Akruti Nirman Ltd. | 701.35 | 180.0 | 74.3% | Verified No Split / Crash |
| INE168O01026 | GCM Commodity & Derivatives Ltd. | 65.0 | 17.45 | 73.2% | Verified No Split / Crash |
| INE325P01011 | Stellar Capital Services Ltd. | 20.1 | 6.16 | 69.4% | Verified No Split / Crash |
| INE019J01013 | Microsec Financial Services Ltd. | 135.1 | 42.0 | 68.9% | Verified No Split / Crash |
| INE030P01017 | Alacrity Securities Ltd. | 12.65 | 4.0 | 68.4% | Verified No Split / Crash |
| INE998H01012 | Oriental Trimex Ltd. | 42.0 | 13.3 | 68.3% | Verified No Split / Crash |
| INE656K01010 | DQ Entertainment (International) Ltd. | 135.0 | 44.5 | 67.0% | Verified No Split / Crash |
| INE871H01011 | GSS America Infotech Ltd. | 400.0 | 134.9 | 66.3% | Verified No Split / Crash |
| INE575I01016 | Rathi Bars Ltd. | 38.0 | 13.08 | 65.6% | Verified No Split / Crash |
| INE369I01014 | Maytas Infra Ltd. | 480.0 | 165.0 | 65.6% | Verified No Split / Crash |
| INE641Q01019 | Carewell Industries Ltd. | 14.4 | 4.96 | 65.6% | Verified No Split / Crash |
| INE322R01022 | Aanchal Ispat Ltd. | 22.1 | 7.62 | 65.5% | Verified No Split / Crash |
| INE982Q01017 | Powerhouse Fitness & Realty Ltd. | 30.0 | 10.37 | 65.4% | Verified No Split / Crash |
| INE123M01017 | RDB Rasayans Ltd. | 85.0 | 32.0 | 62.4% | Verified No Split / Crash |
| INE576P01019 | Karnimata Cold Storage Ltd. | 29.05 | 11.3 | 61.1% | Verified No Split / Crash |
| INE932K01015 | VMS Industries Ltd. | 43.95 | 17.15 | 61.0% | Verified No Split / Crash |
| INE567P01018 | Agrimony Commodities Ltd. | 15.0 | 6.0 | 60.0% | Verified No Split / Crash |
| INE364T01012 | Navigant Corporate Advisors Ltd. | 14.15 | 5.92 | 58.2% | Verified No Split / Crash |
| INE204N01013 | Monarch Health Services Ltd. | 42.0 | 17.9 | 57.4% | Verified No Split / Crash |
| INE807O01011 | Onesource Techmedia Ltd. | 13.0 | 5.54 | 57.4% | Verified No Split / Crash |
| INE172N01012 | Adlabs Entertainment Ltd. | 167.95 | 71.65 | 57.3% | Verified No Split / Crash |
| INE486P01011 | Tentiwal Wire Products Ltd. | 12.5 | 5.4 | 56.8% | Verified No Split / Crash |
| INE106I01010 | Ankit Metal & Power Ltd. | 37.9 | 17.45 | 54.0% | Verified No Split / Crash |
| INE014E01015 | Kovilpatti Lakshmi Roller Flour Mills Ltd. FPO | 55.5 | 25.8 | 53.5% | Verified No Split / Crash |
| INE615T01017 | Ganga Pharmaceuticals Ltd. | 14.5 | 7.13 | 50.8% | Verified No Split / Crash |
| INE812T01010 | Ruby Cables Ltd. | 50.9 | 25.25 | 50.4% | Verified No Split / Crash |
| INE028L21018 | Standard Chartered PLC IDRS | 105.0 | 52.9 | 49.6% | Verified No Split / Crash |
| INE491H01018 | Plethico Pharmaceuticals Ltd. | 245.0 | 366.0 | 49.4% | Verified No Split / Crash |
| INE105R01013 | Funny Software Ltd. | 13.5 | 7.44 | 44.9% | Verified No Split / Crash |
| INE386I01018 | Porwal Auto Components Ltd. FPO | 79.85 | 44.1 | 44.8% | Verified No Split / Crash |
| INE792H01019 | Global Vectra Helicorp Ltd. | 175.0 | 250.0 | 42.9% | Verified No Split / Crash |
| INE210P01015 | Unishire Urban Infra Ltd. | 12.05 | 6.88 | 42.9% | Verified No Split / Crash |
| INE957U01011 | Mewar Hi-Tech Engineering Ltd. | 26.4 | 15.75 | 40.3% | Verified No Split / Crash |
| INE312H01016 | Inox Leisure Ltd. | 285.5 | 172.0 | 39.8% | Verified No Split / Crash |
| INE005I01014 | AMD Metplast Ltd. | 65.1 | 39.9 | 38.7% | Verified No Split / Crash |
| INE583M01012 | Bothra Metals & Alloys Ltd. | 25.5 | 16.0 | 37.3% | Verified No Split / Crash |
| INE990S01016 | Amrapali Fincap Ltd. | 122.3 | 78.0 | 36.2% | Verified No Split / Crash |
| INE009Q01019 | Shri Krishna Prasadam Ltd. | 11.9 | 7.7 | 35.3% | Verified No Split / Crash |
| INE550L01013 | Olympic Cards Ltd. | 29.95 | 19.5 | 34.9% | Verified No Split / Crash |
| INE055L01013 | Acropetal Technologies Ltd. | 130.0 | 92.0 | 29.2% | Verified No Split / Crash |
| INE146Y01013 | Sagar Diamonds Ltd. | 35.55 | 45.0 | 26.6% | Verified No Split / Crash |
| INE344X01016 | Ashok Masala Mart Ltd. | 9.5 | 12.0 | 26.3% | Verified No Split / Crash |
| INE172I01012 | Decolight Ceramics Ltd. | 57.0 | 70.0 | 22.8% | Verified No Split / Crash |
| INE323I01011 | Puravankara Projects Ltd. | 399.0 | 310.0 | 22.3% | Verified No Split / Crash |
| INE165H01018 | Pyramid Saimira Theatre Ltd. | 135.0 | 106.0 | 21.5% | Verified No Split / Crash |
| INE728Z01015 | SoftTech Engineers Ltd. | 72.5 | 88.0 | 21.4% | Verified No Split / Crash |
| INE863I01016 | Bang Overseas Ltd. | 207.0 | 250.0 | 20.8% | Verified No Split / Crash |
| INE0IQ001011 | Veranda Learning Solutions Ltd. | 157.0 | 125.0 | 20.4% | Verified No Split / Crash |