function get_screen_resolution() {
    var width = window.innerWidth
        || document.documentElement.clientWidth
        || document.body.clientWidth;

    var height = window.innerHeight
        || document.documentElement.clientHeight
        || document.body.clientHeight;

    return { "width": width, "height": height }
}

function frozen_cols_checker() {
    dims = get_screen_resolution();
    return dims["width"] > 600;
}

function table_height_large_screen() {
    dims = get_screen_resolution();
    return dims["height"] >= 800 ? "700px" : "500px";
}

function update_table(data) {
    var table = new Tabulator("#example-table", {
        columns: [
            {
                title: "ISIN", field: "isin", frozen: frozen_cols_checker(), headerFilter: true, formatter: "link", formatterParams: {
                    labelField: "isin",
                    urlPrefix: "https://www.google.com/search?q=",
                    target: "_blank",
                }
            },
            { title: "Company", field: "company_name", frozen: frozen_cols_checker(), headerFilter: true },
            { title: "Symbol", field: "symbol", headerFilter: true },
            { title: "Currency", field: "currency", headerFilter: true },
            { title: "Sector", field: "sector", headerFilter: true },
            { title: "Yahoo", field: "yahoo_ticker", headerFilter: true },
            { title: "Report Date", field: "report_date", headerFilter: true },
            { title: "Market Date", field: "market_date", headerFilter: true },
            { title: "Piotroski", field: "p_score", headerFilter: "number", headerFilterFunc: ">=" },
            { title: "ROIC", field: "roic", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "EV/EBITDA Inv", field: "ev_ebitda_ratio_inv", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "SH Yield Stock", field: "shareholder_yield_stock", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "SH Yield Div", field: "shareholder_yield_dividends", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "P/Sales", field: "price_to_sales", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "P/CF", field: "price_to_cash_flow", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "NCAV Ratio", field: "ncav_ratio", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Price", field: "price", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Target Price", field: "target_median_price", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Analyst Opinions", field: "number_of_analyst_opinions", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "EBITDA", field: "ebitda", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Market Cap", field: "market_cap", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Trailing PE", field: "trailing_pe", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Forward PE", field: "forward_pe", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "EV/EBITDA", field: "ev_ebitda_ratio", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "Magic Formula", field: "magic_formula_score", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" }
        ],
        height: table_height_large_screen(),
        data: data,
        autoColumns: false,
        layout: "fitDataFill"
    });

    var dl_link = document.getElementById("download_data_link");
    if (dl_link) {
        dl_link.onclick = function (e) {
            e.preventDefault();
            table.download("csv", "nordic_stocks.csv");
            return false;
        };
    }
}

function loadData() {
    fetch('data.json')
        .then(function (response) { return response.json(); })
        .then(function (data) { update_table(data); })
        .catch(function (err) {
            console.error('Failed to load data:', err);
            document.getElementById('example-table').innerHTML =
                '<p style="padding:20px;color:#666;">Failed to load stock data. The data file may not be available yet.</p>';
        });
}
