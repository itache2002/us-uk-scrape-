# Decisions

## Initial architecture

Date: 2026-09-28  
Problem: The scraper needs resumable discovery and enrichment without a database.  
Decision: Use small Python modules, one Excel workbook for results, and JSON only for configuration and checkpoints.  
Reason: This directly matches the storage constraints while keeping responsibilities testable.

## Discovery source

Date: 2026-09-28  
Problem: Business discovery must support US and UK locations without requiring API credentials.  
Decision: Discover businesses from public search-result pages and use Scrapling for all HTTP page fetching.  
Reason: It provides broad category/location coverage and avoids a required paid API.

## Persistence and deduplication

Date: 2026-09-28  
Problem: Work must survive interruptions and avoid duplicate leads.  
Decision: Save Excel after every processed lead, checkpoint job/query position in JSON, and deduplicate by normalized website domain with normalized name/location as fallback.  
Reason: The workbook remains the source of truth while the checkpoint only tracks progress.

## Concurrency

Date: 2026-09-28  
Problem: Enrichment should be efficient without overwhelming sites or risking workbook corruption.  
Decision: Use bounded thread concurrency for network enrichment and serialize all workbook writes in the main thread.  
Reason: Network work benefits from concurrency; openpyxl writes remain safe and deterministic.

## Scrapling fetcher

Date: 2026-09-28  
Problem: Discovery and enrichment need HTTP fetching without browser overhead.  
Decision: Install Scrapling's `fetchers` extra and use its static `Fetcher` with explicit retries and timeouts.  
Reason: Target pages are server-rendered, so the fastest Scrapling fetcher is sufficient and browser binaries are unnecessary.

## Discovery result filtering

Date: 2026-09-28  
Problem: Search results can include directories and social profiles instead of business websites.  
Decision: Exclude known directory, search, and social hosts before enrichment.  
Reason: Each Excel row should represent a business site, not an aggregator page.

## Discovery source change

Date: 2026-09-28  
Problem: DuckDuckGo HTML returned HTTP 202 with no results during the live smoke test.  
Decision: Use Bing's server-rendered result pages through Scrapling and decode its outbound links.  
Reason: The same live environment returned a populated HTTP 200 page from Bing.

## Country targeting

Date: 2026-09-28  
Problem: Bing localized results to the runner's IP region instead of the requested country.  
Decision: Send explicit US or UK `cc`, `setlang`, and `mkt` search parameters.  
Reason: Job country must control discovery regardless of where the scraper runs.

## OpenStreetMap discovery

Date: 2026-09-28  
Problem: Bing ignored explicit market parameters and returned businesses from the runner's region; Google returned no result cards.  
Decision: Resolve cities with Nominatim and discover category-tagged businesses with Overpass, fetching both through Scrapling.  
Reason: Geographic bounds enforce the requested city/country and mapped businesses may include websites, contacts, or partial data without directory noise.

## Excel safety

Date: 2026-09-28  
Problem: External text beginning with spreadsheet formula characters can execute when opened.  
Decision: Prefix formula-like string cells with an apostrophe before saving.  
Reason: Scraped values remain visible text and cannot become Excel formulas.
