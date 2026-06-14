import pandas as pd
import datetime

# 1. Load the manual overrides
overrides = [
    # ISIN, action_type, raw_subject, ratio_factor, ex_date
    ("INE671T01028", "split", "Face Value Split Rs 10 To Rs 2", 5.0, "2022-06-14"),
    ("INE671T01028", "bonus", "Bonus 11:10", 2.1, "2018-09-19"), # 11 bonus for 10 = 21/10 = 2.1
    ("INE757T01025", "split", "Face Value Split Rs 10 To Rs 1", 10.0, "2023-03-31"),
    ("INE757T01025", "bonus", "Bonus 33:100", 1.33, "2019-03-01"),
    ("INE757T01025", "bonus", "Bonus 3:1", 4.0, "2018-06-01"),
    ("INE757T01025", "bonus", "Bonus 6.5:10", 1.65, "2016-01-01"),
    ("INE0KY201021", "split", "Face Value Split Rs 10 To Rs 1", 10.0, "2024-02-05"),
    ("INE0KY201021", "bonus", "Bonus 1:4", 1.25, "2024-02-05"),
    ("INE191O01010", "bonus", "Bonus 18:10", 2.8, "2014-07-01"),
    ("INE669Y01022", "split", "Face Value Split Rs 10 To Rs 5", 2.0, "2021-08-17"),
    ("INE669Y01022", "bonus", "Bonus 1:1", 2.0, "2021-07-08"),
    ("INE778I01024", "split", "Face Value Split Rs 10 To Rs 5", 2.0, "2010-02-25"),
    ("INE0E4I01027", "split", "Face Value Split Rs 10 To Rs 1", 10.0, "2025-02-14"),
    ("INE899O01018", "bonus", "Bonus 2:1", 3.0, "2011-12-16"),
    ("INE279P01036", "split", "Face Value Split Rs 10 To Rs 1", 10.0, "2016-12-08"),
    ("INE849M01017", "bonus", "Bonus 1:1", 2.0, "2011-07-25"),
    ("INE849M01017", "bonus", "Bonus 1:10", 1.1, "2012-03-20"),
    ("INE442V01012", "bonus", "Bonus 2:1", 3.0, "2021-05-08"),
    ("INE413X01035", "split", "Face Value Split Rs 1 To Rs 10", 0.1, "2024-01-05"),
    ("INE413X01035", "split", "Face Value Split Rs 10 To Rs 1", 10.0, "2022-03-01"),
    ("INE413X01035", "bonus", "Bonus 1:5", 1.2, "2022-11-28"),
    ("INE01A501027", "split", "Face Value Split", 2.0, "2025-04-21"),
    ("INE01A501027", "bonus", "Bonus 1:1", 2.0, "2025-04-02"),
    ("INE700V01021", "split", "Face Value Split", 5.0, "2023-10-27"),
    ("INE700V01021", "bonus", "Bonus 1:5", 1.2, "2018-10-12"),
    ("INE541R01019", "bonus", "Bonus 1:3", 1.333, "2024-07-12"),
    ("INE541R01019", "bonus", "Bonus 1:5", 1.2, "2018-10-06"),
    ("INE541R01019", "bonus", "Bonus 3:2", 2.5, "2016-04-08"),
    ("INE00TV01023", "split", "Face Value Split", 10.0, "2024-11-22"),
    ("INE030U01025", "split", "Face Value Split", 2.0, "2017-02-02"),
    ("INE030U01025", "bonus", "Bonus 1:1", 2.0, "2020-10-07"),
    ("INE552Q01018", "split", "Face Value Split", 10.0, "2015-03-01"),
    ("INE084Q01012", "bonus", "Bonus 20:1", 21.0, "2013-11-01"),
    ("INE973X01012", "bonus", "Bonus 1:1", 2.0, "2020-01-02")
]

# Write to manual overrides file
df_override = pd.DataFrame(overrides, columns=['isin', 'action_type', 'raw_subject', 'ratio_factor', 'ex_date'])
df_override['source'] = 'manual_thinktank_audit'
df_override['symbol'] = 'MANUAL' # Doesn't matter, we match on ISIN

df_merged = pd.read_csv('data/reference/corp_actions_merged.csv')

# Drop any existing manual overrides to prevent duplicates
df_merged = df_merged[df_merged['source'] != 'manual_thinktank_audit']

# Append
df_final = pd.concat([df_merged, df_override], ignore_index=True)
df_final.to_csv('data/reference/corp_actions_merged.csv', index=False)
print(f"Added {len(overrides)} manual overrides. Re-running returns summary...")

