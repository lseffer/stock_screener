from utils.alembic_helpers import ReplaceableObject

PiotroskiScore = ReplaceableObject(
    "piotroski_score",
    """
SELECT
    isin,
    report_date,
    CASE
        WHEN p_score_1
        THEN 1
        ELSE 0
    END AS p_score_1,
    CASE
        WHEN p_score_2
        THEN 1
        ELSE 0
    END AS p_score_2,
    CASE
        WHEN p_score_3
        THEN 1
        ELSE 0
    END AS p_score_3,
    CASE
        WHEN p_score_4
        THEN 1
        ELSE 0
    END AS p_score_4,
    CASE
        WHEN p_score_5
        THEN 1
        ELSE 0
    END AS p_score_5,
    CASE
        WHEN p_score_6
        THEN 1
        ELSE 0
    END AS p_score_6,
    CASE
        WHEN p_score_7
        THEN 1
        ELSE 0
    END AS p_score_7,
    CASE
        WHEN p_score_8
        THEN 1
        ELSE 0
    END AS p_score_8,
    CASE
        WHEN p_score_9
        THEN 1
        ELSE 0
    END AS p_score_9,
    CASE
        WHEN p_score_1
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_2
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_3
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_4
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_5
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_6
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_7
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_8
        THEN 1
        ELSE 0
    END +
    CASE
        WHEN p_score_9
        THEN 1
        ELSE 0
    END AS p_score
FROM
    (
        SELECT
            isin,
            report_date,
            COALESCE(return_on_assets > 0, FALSE) AS p_score_1,
            COALESCE(total_cash_from_operating_activities > 0.0, FALSE) AS p_score_2,
            COALESCE(return_on_assets > LAG(return_on_assets) OVER (PARTITION BY isin ORDER BY report_date ASC), FALSE
            ) AS p_score_3,
            COALESCE(total_cash_from_operating_activities > net_income, FALSE) AS p_score_4,
            COALESCE(long_term_debt < LAG(long_term_debt) OVER (PARTITION BY isin ORDER BY report_date ASC), FALSE) AS
            p_score_5,
            COALESCE(current_ratio > LAG(current_ratio) OVER (PARTITION BY isin ORDER BY report_date ASC), FALSE) AS
            p_score_6,
            COALESCE(net_shares_issued <= 0, FALSE) AS p_score_7,
            COALESCE(gross_margin_pct > LAG(gross_margin_pct) OVER (PARTITION BY isin ORDER BY report_date ASC), FALSE
            ) AS p_score_8,
            COALESCE(asset_turnover > LAG(asset_turnover) OVER (PARTITION BY isin ORDER BY report_date ASC), FALSE) AS
            p_score_9
        FROM
            (
                SELECT
                    isin,
                    report_date,
                    (total_revenue - cost_of_revenue) / NULLIF(total_revenue, 0) AS gross_margin_pct,
                    total_current_assets / NULLIF(total_current_liabilities, 0) AS current_ratio,
                    total_revenue / (
                        CASE
                            WHEN LAG(total_assets) OVER (PARTITION BY isin ORDER BY report_date ASC) IS NULL
                            THEN total_assets
                            ELSE (LAG(total_assets) OVER (PARTITION BY isin ORDER BY report_date ASC) + total_assets)
                                / 2
                        END) AS asset_turnover,
                    COALESCE(issuance_of_stock, 0.0) + COALESCE(repurchase_of_stock, 0.0) AS net_shares_issued,
                    a.net_income / NULLIF(total_assets, 0) AS return_on_assets,
                    total_cash_from_operating_activities,
                    a.net_income,
                    long_term_debt
                FROM
                    income_statements AS a
                FULL JOIN
                    cash_flow_statements AS b
                USING
                    (isin, report_date)
                FULL JOIN
                    balance_sheet_statements AS c
                USING
                    (isin, report_date) ) AS a) AS a
    """
)
