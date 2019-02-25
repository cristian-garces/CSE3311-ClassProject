let roles_table = null;
let queries = {};
let data_table_element = null;
let role_description = $("#role-description");
let role_description_map = {
    "": "Selection column, allows group checking or un-checking",
    "Name": "A user's name as stored in our database",
    "Net ID": "A user's UTA administered Net ID (e.g., axb1234)",
    "STF": "CSE staff",
    "FINANCE": "CSE accounting staff",
    "UAD": "Undergraduate advisor",
    "GAD": "Graduate advisor",
    "STFADM": "CSE staff administrator",
    "FAD": "Faculty administrator (i.e., Chair and Associate Chair)",
    "ABETADM": "ABET administrator",
    "DEV": "CSE website developer"
};

function toggleQuery(key, queries_object, net_id, role, checked) {
    if (key in queries_object) {
        delete queries_object[key];
    }
    else {
        queries_object[key] = {
            net_id: net_id,
            role: role,
            action: (checked === true ? "add" : "delete")
        };
    }
}

function checkboxClicked(element) {
    let user = roles_table.row(element.parents('tr')).data();
    let columns = roles_table.settings().init().columns;
    let column_index = roles_table.cell(element.parents('td')).index().column;
    let selected_cell = roles_table.cell(element.parents('tr'), element.parents('td'))[0][0];
    let dict_key = selected_cell.row + "," + selected_cell.column;
    let is_checked = element[0].checked;
    let selected_rows = roles_table.rows({selected: true})[0];

    toggleQuery(dict_key, queries, user.net_id, columns[column_index].name, is_checked);
    if (selected_rows.length > 0 && $.inArray(selected_cell.row, selected_rows) > -1) {
        $.each(roles_table.rows({selected: true})[0], function (index, value) {
            if (is_checked === !$(roles_table.cell(value, selected_cell.column).node()).find("input").prop("checked")) {
                let selected_user = roles_table.row(value).data();
                dict_key = value + "," + selected_cell.column;
                $(roles_table.cell(value, selected_cell.column).node()).find("input").prop("checked", is_checked);

                toggleQuery(dict_key, queries, selected_user.net_id, columns[column_index].name, is_checked);
            }
        });
    }
}

$(document).ready(function () {
    $("thead > tr > th").hover(
        function (e) {
            role_description.html(role_description_map[this.textContent]);
        },
        function (e) {
            role_description.html('<i class="fas fa-info-circle mr-2"></i> Scroll over any column head to see it\'s description here.');
        }
    );

    roles_table = $("#user_table").DataTable({
        language: {
            emptyTable: "",
            zeroRecords: "",
            processing: '<i class="fas fa-cog fa-spin mr-3" data-fa-transform="grow-9"></i> Loading Data',
            loadingRecords: ""
        },
        lengthMenu: [[10, 25, 50, 100, 300, -1], [10, 25, 50, 100, 300, "All"]],
        ajax: {
            url: "./get/data",
            dataSrc: ""
        },
        processing: true,
        deferRender: true,
        columns: [
            {
                orderable: false,
                className: "select-checkbox align-middle",
                data: null,
                defaultContent: ""
            },
            {
                data: "name",
                className: "align-middle"
            },
            {
                data: "net_id",
                className: "align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.STF) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.STF;
                    }
                },
                name: "STF",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.FINANCE) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.FINANCE;
                    }
                },
                name: "FINANCE",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.UAD) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.UAD;
                    }
                },
                name: "UAD",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.GAD) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.GAD;
                    }
                },
                name: "GAD",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.STFADM) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.STFADM;
                    }
                },
                name: "STFADM",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.FAD) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.FAD;
                    }
                },
                name: "FAD",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.ABETADM) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.ABETADM;
                    }
                },
                name: "ABETADM",
                className: "role-td align-middle"
            },
            {
                render: function (data, type, row, meta) {
                    if (type === "display") {
                        if (row.DEV) {
                            return '<div class="custom-control custom-checkbox center-checkbox">' +
                                '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '" checked/>' +
                                '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                                '</div>';
                        }
                        return '<div class="custom-control custom-checkbox center-checkbox">' +
                            '   <input class="role-checkbox custom-control-input" type="checkbox" id="' + meta.row + ',' + meta.col + '"/>' +
                            '   <label class="custom-control-label" for="' + meta.row + ',' + meta.col + '"></label>' +
                            '</div>';
                    }
                    else {
                        return row.DEV;
                    }
                },
                name: "DEV",
                className: "role-td align-middle"
            }
        ],
        select: {
            style: 'multi+shift',
            selector: 'td:first-child'
        },
        order: [[1, 'asc']]
    });
    data_table_element = $("#user_table tbody");

    data_table_element.on('click', 'input.role-checkbox', function (e) {
        checkboxClicked($(this));
    });

    data_table_element.on('click', 'td.role-td', function (e) {
        let checkbox = $(this).find("input");

        checkbox.prop("checked", !checkbox[0].checked);
        checkboxClicked(checkbox);
    });

    $("#save-button").click(function (e) {
        if (!$.isEmptyObject(queries)) {
            $.ajax({
                type: 'POST',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify(queries, null, "\t"),
                url: "./",
                dataType: "json",
                success: function (data) {
                    toastr[data.type](data.message);
                }
            });
        }
        else {
            toastr["error"]("No changes have been selected.");
        }
    });

    $(".select-filter").change(function (e) {
        let selected_filter = $(this).find("option:selected")[0].text.toLowerCase();

        if (selected_filter.indexOf("filter users") < 0) {
            roles_table.clear().draw();
            queries = {};
            roles_table.ajax.url("./get/data/" + selected_filter);
            roles_table.ajax.reload();
            data_table_element = $("#user_table tbody");
        }
    });
});
