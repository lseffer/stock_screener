function ajax_get(url, callback) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            console.log('responseText:' + xmlhttp.responseText);
            try {
                var data = JSON.parse(xmlhttp.responseText);
            } catch (err) {
                console.log(err.message + " in " + xmlhttp.responseText);
                return;
            }
            callback(data);
        }
    };

    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

//define table
function update_table(data) {

    var table = new Tabulator("#example-table", {
        columns: [
            {
                title: "isin", field: "isin", frozen: true, headerFilter: true, formatter: "link", formatterParams: {
                    labelField: "isin",
                    urlPrefix: "https://www.google.com/search?q=",
                    target: "_blank",
                }
            },
            { title: "company_name", field: "company_name", frozen: true, headerFilter: true },
            { title: "symbol", field: "symbol", headerFilter: true },
            { title: "currency", field: "currency", headerFilter: true },
            { title: "sector", field: "sector", headerFilter: true },
            { title: "yahoo_ticker", field: "yahoo_ticker", headerFilter: true },
            { title: "report_date", field: "report_date", headerFilter: true },
            { title: "market_date", field: "market_date", headerFilter: true },
            { title: "p_score", field: "p_score", headerFilter: "number", headerFilterFunc: ">=" },
            { title: "roic", field: "roic", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "ev_ebitda_ratio_inv", field: "ev_ebitda_ratio_inv", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "shareholder_yield_stock", field: "shareholder_yield_stock", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "shareholder_yield_dividends", field: "shareholder_yield_dividends", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "price_to_sales", field: "price_to_sales", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "price_to_cash_flow", field: "price_to_cash_flow", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "ncav_ratio", field: "ncav_ratio", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "price", field: "price", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "target_median_price", field: "target_median_price", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "number_of_analyst_opinions", field: "number_of_analyst_opinions", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "ebitda", field: "ebitda", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "market_cap", field: "market_cap", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "trailing_pe", field: "trailing_pe", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "forward_pe", field: "forward_pe", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "ev_ebitda_ratio", field: "ev_ebitda_ratio", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" },
            { title: "magic_formula_score", field: "magic_formula_score", headerFilter: "number", headerFilterFunc: ">=", formatter: "money" }
        ],
        height: "500px",
        data: data,
        autoColumns: false,
        layout: "fitDataFill",
        persistenceMode: "cookie"
    });

    var dl_link = document.getElementById("download_data_link");

    dl_link.onclick = function (e) {
        e.preventDefault();
        table.download("csv", "data.csv");
        return false;
    }
};

function reload_table_onclick(e) {
    e.preventDefault();
    reload_table();
    return false;
};

function reload_table() {
    ajax_get('./stocks', function (data) {
        update_table(data)
    });
};

function logout_onclick(e) {
    e.preventDefault();
    xhr = new XMLHttpRequest();
    xhr.open("POST", "logout", true);
    xhr.onload = function () {
        location.reload();
    };
    xhr.send();
};
