---
title: Seasonal Demand Drivers — Shapewear & Intimates
sources:
  - en_wikipedia_org_wiki_Shapewear.md
  - en_wikipedia_org_wiki_Spanx.md
  - en_wikipedia_org_wiki_Skims.md
  - skims_com_collections_shapewear.md
  - skims_com_collections_loungewear.md
  - skims_com_collections_swim.md
  - nrf_com_topics_holiday_and_seasonal_trends.md
  - nrf_com_research_monthly_retail_trade.md
updated: 2026-05-02
---

# Seasonal Demand Drivers — Shapewear & Intimates

## Seasonal Demand Patterns

Shapewear and intimates demand is meaningfully seasonal, even though the products themselves are largely non-weather-dependent. Three windows do most of the work in a typical year. The first is Q4 — October through December — when holiday gifting drives intimates volume and Census MRTS for NAICS 448/4481 spikes well above its trend line; the NRF's holiday and seasonal-trends research is the canonical source for this pattern even though that page currently returns a 404, and the same seasonality is reproducible in the project's `fact_retail_sales` mart from Census MRTS. The second is February, where Valentine's Day pulls forward demand for bras, lingerie, and giftable lounge sets — a window SKIMS now activates explicitly (per the Wikipedia *Skims* entry, BLACKPINK's Rosé fronted SKIMS' Valentine's Day 2025 campaign). The third is mid-summer (May–July) for swim and lightweight intimates; SKIMS' Iconic Swim and Signature Swim collections (skims.com/collections/swim) and its lightweight cotton brief lines are positioned to land in spring resort floor sets and sell through summer vacations.

For shapewear specifically, the layered demand curve is a little different from broader intimates. Wikipedia's *Foundation garment* (Shapewear) entry frames shapewear as outfit-driven — worn under specific dresses, suits, and going-out looks — which means it indexes hard to event seasons (holiday parties in November–December, wedding season in May–September, Mother's Day in May, prom in April–May) and to back-to-work / back-to-school silhouette resets in late August and early January. Loungewear, by contrast, builds heavily into Q4 gifting and a second peak in January as consumers buy comfort goods for themselves at the start of the year.

## Q4 and Holiday Dynamics

Q4 is the planning year for an intimates and shapewear business. Holiday gifting concentrates demand into roughly eight weeks, with Black Friday/Cyber Monday acting as the demand tipping point and the two weeks before Christmas pulling the residual gift volume. The NRF's holiday-trends research consistently shows apparel and accessories among the most-gifted hard-good categories, and intimates have moved up that list as brands have made the category more giftable through better packaging, gift sets, and broadened color/print stories. SKIMS' Soft Lounge Sleep Set ($128) and the Cotton Fleece Classic Hoodie/Jogger duo (each $88; skims.com/collections/loungewear) are explicit Q4 gift hero SKUs designed to land at the Black Friday price-promotion window.

Promotionally, SKIMS' historical Q4 playbook is restraint relative to peers: limited sitewide markdowns, drops timed to landmark dates (the brand's BFCM activations and seasonal capsule launches drive most of the lift), and celebrity-led content amplification through the Kardashian-Jenner social footprint and partner channels (NBA/WNBA in-arena exposure, per Wikipedia's *Skims* entry). Spanx's recent playbook — Allyson Felix-fronted global campaigns, denim and apparel launches, ABC News-amplified spring-arrivals coverage (referenced in Wikipedia, *Spanx*) — leans more conventionally promotional and wholesale-tied. The contrast matters for forecasting: SKIMS' Q4 is more concentrated and depends more heavily on a few hero SKUs hitting their sell-through targets, while a Spanx-style book is more distributed across wholesale partners and depths.

## Inventory Challenges

Apparel inventory planning runs on long lead times — typically 6 to 8 weeks for in-season replenishment of basics (longer for new-season cut-and-sew and complex constructions), which means a Planning Analyst is committing to most of the holiday buy in the summer with limited ability to chase demand in November. Shapewear amplifies this constraint structurally because the category's SKU count is high relative to revenue: each style is multiplied by an unusually wide size range (SKIMS: XXS–5XL; Spanx: XS–3X per their Wikipedia entries), an unusually wide tonal range (nine SKIMS shades to match skin tones, per Wikipedia, *Skims*), and a layered support-level range (SKIMS shapewear is segmented into Light, Mid, Firm, and Maximum compression sub-collections — SKIMS Body, Seamless Sculpt, Sheer Sculpt, Sheer Seamless, and Waist Trainers — per skims.com/collections/shapewear). The same hero bodysuit can therefore live as 60+ SKUs once size and shade are exploded, and each one of those SKUs has its own demand curve.

The downstream consequence is markdown risk in trough months — typically January–February for shapewear (post-holiday) and August–September (between back-to-school sweats and Q4 gifting). Aged inventory on a single shade-size in a hero style cannot be easily redistributed, which is why broken-size analytics, color-tone sell-through ratios, and reorder velocity by sub-collection are the three numbers that move most of an intimates planner's day. Cotton-based and seamless-construction items (the bulk of SKIMS' Lightweight Cotton underwear and Fits Everybody bra programs) carry less markdown risk than novelty prints and limited capsule collaborations like FENDI x SKIMS or Nike x SKIMS, which are inherently single-season.

## Demand Signals for Planning

The day-to-day signal stack for a Planning Analyst on this category reads roughly as follows: weekly sell-through rate by style and size, week-over-week reorder velocity on hero SKUs, color/shade ratio versus plan, return rate (especially elevated in shapewear due to fit), and as a macro overlay, the monthly Census MRTS series for NAICS 448 and 4481 read in trend (12-month rolling) and YoY terms. The Census series is the same one published by the US Census Bureau Monthly Retail Trade Survey and the same one feeding this project's `fact_retail_sales` table — `month_over_month_change` and `year_over_year_change` columns on that table are the macro-comp signal that contextualizes a brand's own sell-through. When the Census YoY for NAICS 4481 turns negative for two consecutive months, the planner's working assumption shifts from "we are missing reorders" to "the category is off and we should pull receipts" — a distinction that matters more in shapewear than almost any other apparel sub-category, because once size-shade SKU depth is on the floor it cannot be unbought.
