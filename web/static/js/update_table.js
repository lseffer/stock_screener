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
        pagination: "local", //enable local pagination.
        height: "500px",
        data: data,
        autoColumns: true,
        layout: "fitDataFill"
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
