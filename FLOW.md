# System Flow

Input (CLI or JSON jobs)  
↓  
City geocoding (Nominatim via Scrapling)  
↓  
Business discovery (Overpass via Scrapling)  
↓  
Normalize discovery results  
↓  
Remove duplicates  
↓  
Website found?  
├─ No → Save available data  
└─ Yes  
↓  
Scrapling website enrichment  
↓  
Relevant contact/about pages  
↓  
Email / phone / social extraction  
↓  
Clean and normalize data  
↓  
Quality score  
↓  
Excel save  
↓  
JSON checkpoint

## Module flow
 
`main.py` → `config` parses jobs → `runner` coordinates work → `discovery` yields businesses → `dedupe` filters known leads → `enrichment` fetches sites → `extractors` finds contacts → `cleaning` normalizes fields → `enrichment.score` grades leads → `excel` saves rows → `checkpoint` records resumable progress.
