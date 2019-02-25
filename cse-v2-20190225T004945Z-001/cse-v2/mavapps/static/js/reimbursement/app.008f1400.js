const uploaded_file_list = $("#uploaded-files-list");
const no_files_message = uploaded_file_list.find("p");
const request_form = $("#request-info");
const current_total = $("#current-total");
const pay_to_cse = $(".payto-cse-member");
const pay_to_noncse = $(".payto-non-cse");
const pay_to_selected = $(".pay_to_selected");
const travel_request_div = $(".travel-request");
const travel_request_inputs = travel_request_div.find("input");
const travel_from = $(".travel-from");
const travel_to = $(".travel-to");
const last_autosave_text = $("#last-autosave");
let new_request_folder = createUniqueFolderName();
let payee_name = "";
let payee_email = "";
let file_selector_map = {};
let file_details = {};
let permanent_delete = true;

window.onbeforeunload = function () {
    if (window.location.pathname.indexOf("/new/") > -1 || window.location.pathname.indexOf("/edit/") > -1) {
        saveOrSubmit(true);
        return undefined;
    }
};

function cancelRequest(show_toast=true, flash_message=false) {
    $.ajax({
        type: 'DELETE',
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({user_id: null, folder_name: new_request_folder, delete_request: true, flash_message: flash_message}, null, "\t"),
        url: "../../",
        dataType: "json",
        success: function (data) {
            if (show_toast) {
                toastr[data.type](data.message);
            }
        }
    });
}

function downloadHelper(details_container, pdf=false, file_name=null){
    getRequestFiles(
        details_container.find("#requester-net-id").text(),
        details_container.find("#request-id").text(),
        details_container.find("#request-month").text() + "_" +
        details_container.find("#request-day").text() + "_"+
        details_container.find("#request-year").text(),
        pdf, file_name
    );

    return false;
}

function getRequestFiles(user_id, request_id, request_date, pdf=false, file_name=null) {
    let xhr = new XMLHttpRequest();

    if (pdf) {
        xhr.open('GET', "../../download/pdf/" + user_id + "/" + request_id + "/" + request_date, true);
    }
    else if (file_name) {
        xhr.open('GET', "../../download/file/" + user_id + "/" + request_id + "/" + file_name, true);
    }
    else {
        xhr.open('GET', "../../download/" + user_id + "/" + request_id + "/" + request_date, true);
    }
    xhr.responseType = 'blob';


    xhr.onload = function(e) {
        if (this.status === 200) {
            let blob = this.response;
            if (pdf) {
                saveAs(blob, "(" + user_id + "--" + request_date + ")__report.pdf");
            }
            else if (file_name) {
                let original_file_name = file_name.split(".");

                original_file_name = original_file_name.slice(0, -2).concat(original_file_name.slice(-1));
                saveAs(blob, original_file_name.join(".").trim());
            }
            else {
                saveAs(blob, "(" + user_id + "--" + request_date + ")__request.zip");
            }
        }
        else {
            toastr["error"]("Unable to download file. If the problem persists, contact the administrator.");
        }
    };

    xhr.send();
}

function toggleProcessRequest(element) {
    let request_div = getNthParent($(element), 3).siblings("div.request-div");
    let request_container_link = request_div.find("a");
    let is_processed = request_div.attr("data-request-processed") === "true";

    if(is_processed) {
        $(element).html('<i class="far fa-square text-danger" data-fa-transform="grow-6"></i>');
        $(element).popup({position: "bottom center", html: "<b>Process Request</b>", variation: "tiny"});
        request_div.attr("data-request-processed", "false");
    }
    else {
        $(element).html('<i class="far fa-check-square text-success" data-fa-transform="grow-6"></i>');
        $(element).popup({position: "bottom center", html: "<b>Unprocess Request</b>", variation: "tiny"});
        request_div.attr("data-request-processed", "true");
    }

    is_processed = !is_processed;

    if (is_processed) {
        request_container_link.removeClass("uta-blue-bg");
        request_container_link.addClass("uta-orange-bg");
    }
    else {
        request_container_link.removeClass("uta-orange-bg");
        request_container_link.addClass("uta-blue-bg");
    }

    return is_processed;
}

function processRequest(user_id, request_id, processed, element, req_return_btn, req_void_btn) {
    let form_title = null;
    let form = null;
    let payload = {};

    if (processed) {
        form_title = "Process Request";
        form = ['<label for="transactionNumber">Transaction Number</label>' +
                '<input name="transactionNumber" type="text" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" aria-label="Transaction Number" placeholder="UT Share, etc." required>' +
                '<label for="userMessage">Notes</label>' +
                '<textarea name="userMessage" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" rows="8" placeholder="Optional message to provide the user…"></textarea>'
        ].join('');
    }
    else {
        form_title = "Unprocess Request";
        form = ['<label for="userMessage">Message</label>' +
                '<textarea name="userMessage" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" rows="10" aria-label="Message" placeholder="Reason for unprocessing the request…" required></textarea>'
        ].join('');
    }

    vex.dialog.open({
        message: form_title,
        input: form,
        buttons: [
            $.extend({}, vex.dialog.buttons.YES, { text: processed ? "PROCESS": "UNPROCESS" }),
            $.extend({}, vex.dialog.buttons.NO, { text: "CANCEL" })
        ],
        callback: function(data) {
            if (data) {
                if (processed){
                    payload.transaction_number = data["transactionNumber"];
                }
                payload.message = data["userMessage"];

                $.ajax({
                    type: 'POST',
                    contentType: 'application/json;charset=UTF-8',
                    data: JSON.stringify(payload, null, "\t"),
                    url: "../../process/" + user_id + "/" + request_id + "/" + String(processed),
                    dataType: "json",
                    success: function (data) {
                        if (!data.success) {
                            toggleProcessRequest(element);
                        }
                        else {
                            req_void_btn.toggleClass("d-none");
                            req_return_btn.toggleClass("d-none")
                        }

                        toastr[data.type](data.message);
                    }
                });
            }
            else {
                toggleProcessRequest(element);
            }
        }
    });
}

function saveOrSubmit(save_for_later=false, resubmit_message="") {
    requestTotalSanityCheck();

    let current_date = new Date();
    let request_account = $("#request-account");
    let payload = {
        folder_name: new_request_folder,
        processed: false,
        requester: current_user,
        request_date: {
            year: current_date.getFullYear(),
            month: (current_date.getMonth() + 1),
            day: current_date.getDate(),
            weekday: weekday_map[current_date.getDay()],
            hours: current_date.getHours(),
            minutes: current_date.getMinutes(),
            seconds: current_date.getSeconds()
        },
        short_description: $("#request-title").val(),
        account_number: request_account.val(),
        account_description: request_account.find("option:selected").text().split(":").slice(1).join(":").trim(),
        principal_investigator: current_user.net_id,
        notes: $("#request-special-notes").val(),
        total_amount: parseFloat(current_total.text())
    };

    if ($("#no-id-switch").prop("checked")) {
        payload.external_payee = true;
        payload.pay_to = {
            name: $("#request-payto-name").val(),
            email: $("#request-payto-email").val(),
            id: null
        };
    }
    else {
        payload.external_payee = false;
        payload.pay_to = {
            name: payee_name,
            email: payee_email,
            id: $("#request-payto").val()
        };
    }

    if ($("#request-type").val() === "Travel") {
        let travel_from_location = travel_from.search("get result").full_location;
        let travel_to_location = travel_to.search("get result").full_location;
        let travel_from_input = $("#travel-from-search");
        let travel_to_input = $("#travel-to-search");

        payload.request_type = "travel";
        payload.travel_from = travel_from_input.val() === travel_from.search("get value")  && travel_from_location ? travel_from_location.city + ", " + travel_from_location.state + ", " + travel_from_location.country: travel_from_input.val();
        payload.travel_from_date = $("#travel-from-date").val();
        payload.travel_to = travel_to_input.val() === travel_to.search("get value")  && travel_to_location ? travel_to_location.city + ", " + travel_to_location.state + ", " + travel_to_location.country: travel_to_input.val();
        payload.travel_to_date = $("#travel-to-date").val();
        payload.travel_number = $("#travel-number").val();
        payload.event_website = htmlDecode($("#event-website").val());
        payload.ctp_checkbox_checked = $("#ctp-receipts-provided-checkbox").prop('checked');
    }
    else {
        payload.request_type = "general";
    }

    payload.files = [];

    $.each(file_selector_map, function(key, value) {
        let file = value.get(0).file;

        if (file.status === "success") {
            payload.files.push({
                name: file.name,
                short_name: file.name.length > 31 ? file.name.slice(0, 20) + "…" + file.name.slice(-10): file.name,
                label: htmlDecode(file.userLabel),
                description: htmlDecode(file.userDescription.replace(/<br>/gm, "\n")),
                dollar_amount: file.dollarAmount,
                type: file.type,
                size: file.size,
                upload: file.upload
            });
        }
    });

    payload.history = [];

    $.ajax({
        type: 'PUT',
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({
            folder_name: new_request_folder,
            request_details: payload,
            save_for_later: save_for_later,
            user_message: resubmit_message
        }, null, "\t"),
        url: "../../",
        dataType: "json",
        success: function (response) {
            if (!save_for_later || (save_for_later && response["status"] === false)) {
                window.onbeforeunload = null;
                window.location.replace("../../");
            } else {
                last_autosave_text.html('<i class="fas fa-exclamation-circle"></i> Last auto-save: ' + getFormattedDate() + ' - ' + getFormmatedTime());
            }
        }
    });
}

function canonizeName(fileName) {
    let date = new Date();
    let rev_split_fileName = fileName.split(".").reverse();

    rev_split_fileName.splice(1, 0, "" + date.getDate() + date.getDay() + date.getHours() + date.getMinutes() + date.getSeconds() + date.getMilliseconds());
    rev_split_fileName = rev_split_fileName.reverse().join(".");

    return rev_split_fileName;
}

function requestTotalSanityCheck() {
    let calculated_total = 0.0;
    let on_screen_total = parseFloat(current_total.text());

    $("div#uploaded-files-list a.list-group-item p:nth-child(4) i").each(function(e) {
        calculated_total += parseFloat(this.innerText.replace("$", ""));
    });

    if (calculated_total !== on_screen_total) {
        current_total.text((calculated_total).toFixed(2));
    }
}

Dropzone.options.reimbursementDropzone = {
    dictRemoveFileConfirmation: null,
    dictDefaultMessage: "Click or drop files here to upload <i class=\"fa fa-upload\" aria-hidden=\"true\"></i><br><small>(.txt, .doc, .docx, .xls, .xlsx, .pdf, .png, .jpg, .jpeg, .gif, .zip)</small>",
    paramName: "file",
    headers: {"folder_name": new_request_folder},
    maxFilesize: 50, // MB
    maxThumbnailFilesize: 20, // MB
    addRemoveLinks: true,
    init: function() {
        // .removeAllFiles(true) remove all files and cancel any uploading ones
        let current_dropzone = this;

        this.on("complete", function(file) {
            $.each(this.getRejectedFiles(), function() {
                if(this === file) {
                    $(file.previewElement).fadeOut(333);
                    $(file_selector_map[file.upload.filename]).fadeOut(333);

                    setTimeout(function() {
                        current_dropzone.removeFile(file);
                        $(file_selector_map[file.upload.filename]).remove();
                        delete file_selector_map[file.upload.filename];
                        delete file_details[file.upload.filename];
                    }, 250);
                }
            });
        });

        this.on("error", function(file) {
            $.each(this.getRejectedFiles(), function(){
                if(this === file) {
                    $(file.previewElement).fadeOut(333);
                    $(file_selector_map[file.upload.filename]).fadeOut(333);

                    setTimeout(function() {
                        current_dropzone.removeFile(file);
                        $(file_selector_map[file.upload.filename]).remove();
                        delete file_selector_map[file.upload.filename];
                        delete file_details[file.upload.filename];
                    }, 250);
                }
            });
        });

        this.on("success", function(file, data) {
            if(data !== null && data.success === false) {
                file.accepted = false;
                toastr[data.type](file.name + ": " + data.message);
                $(file.previewElement).fadeOut(333);

                setTimeout(function() {
                    current_dropzone.removeFile(file);
                }, 250);
            }
            else {
                no_files_message.hide();
                let fName = file.name.length > 31 ? file.name.slice(0, 20) + "…" + file.name.slice(-10): file.name;
                let fLabel = file.userLabel.length > 15 ? file.userLabel.slice(0, 8) + "…" + file.userLabel.slice(-5): file.userLabel;
                let amount_text = "";

                if (data !== null) {
                    file.upload.filename = data.filename;
                }

                if (file.dollarAmount.toFixed(2) > 0.0) {
                    amount_text = '' +
                        '    <p>' + 'Amount: ' +
                        '        <i class="not-italic text-success text-shadow">$' + file.dollarAmount.toFixed(2) +
                        '        </i>' +
                        '    </p>';
                }
                else {
                    amount_text = '<span class="badge badge-light margin-auto-0 no-margin-t">Auxiliary File</span>';
                }

                file_selector_map[file.upload.filename] = $('' +
                    '<a href="#" class="list-group-item list-group-item-action flex-column align-items-start active">' +
                    '    <div class="d-flex w-100 justify-content-between mb-2">' +
                    '        <h5>' + (data !== null ? escapeHtml(fName) : fName) + '</h5>' +
                    '        <span class="badge badge-light margin-auto-0 no-margin-t">' + (data !== null ? escapeHtml(fLabel) : fLabel) + '</span>' +
                    '    </div>' +
                    '    <p class="mb-2">' + (data !== null ? escapeHtml(file.userDescription).replace(/\n/gm, "<br>") : file.userDescription.replace(/\n/gm, "<br>")) + '</p>' +
                    '    <button role="button" class="btn btn-link base-link-white download-file mb-2" file-name="' + fName + '"><i class="fas fa-download mr-0" data-fa-transform="grow-5"></i></button>' +
                    amount_text +
                    '</a>');

                file_selector_map[file.upload.filename].appendTo(uploaded_file_list);
                file_selector_map[file.upload.filename].get(0).file = file;
                $(file_selector_map[file.upload.filename].get(0)).find("button").popup({position: "bottom center", html: "<b>Download File</b>", variation: "tiny"});

                $(file_selector_map[file.upload.filename]).click(function(e) {
                    e.preventDefault();

                    if ($(e.target).is("button.download-file") || $(e.target).is("svg") || $(e.target).is("path")) {
                        getRequestFiles(current_user.net_id, new_request_folder, null, false, file.upload.filename);
                    } else {
                        let file_pointer = $("#file-pointer");
                        let file_icon_position = $($(this).get(0).file.previewElement).position();
                        let file_icon_height = $($(this).get(0).file.previewElement).height();

                        file_pointer.finish();
                        file_pointer.hide();

                        file_pointer.css({
                            "top": (file_icon_position.top + Math.ceil(file_icon_height / 2) - 18) + "px",
                            "left": (file_icon_position.left - 12) + "px"
                        });

                        file_pointer.fadeIn(1000).delay(2000).fadeOut(1000);
                    }
                });

                if(data !== null) {
                    toastr[data.type](file.name + ": " + data.message);
                }
            }
        });

        this.on("removedfile", function(file) {
            let file_pointer = $("#file-pointer");

            file_pointer.finish();
            file_pointer.hide();
            $(file_selector_map[file.upload.filename]).fadeOut(333);

            setTimeout(function() {
                $(file_selector_map[file.upload.filename]).remove();
                delete file_selector_map[file.upload.filename];
                delete file_details[file.upload.filename];
                current_total.text((parseFloat(current_total.text()) - (file.dollarAmount ? file.dollarAmount : 0)).toFixed(2));

                if(uploaded_file_list.children().length < 2) {
                    no_files_message.delay(333).show();
                }
            }, 250);

            if(file.accepted) {
                $.ajax({
                    type: 'DELETE',
                    contentType: 'application/json;charset=UTF-8',
                    data: JSON.stringify({file: file.upload.filename, folder_name: new_request_folder, delete_request: false}, null, "\t"),
                    url: "../../",
                    dataType: "json",
                    success: function (data) {
                        toastr[data.type](file.name + ": " + data.message);
                    }
                });
            }
        });
    },
    accept: function(file, done) {
        file.upload.filename = canonizeName(file.upload.filename);
        let fName = file.name.length > 65 ? file.name.slice(0, 54) + "…" + file.name.slice(-10): file.name;

        vex.dialog.open({
            message: "File Details",
            input: [
                '<label for="userLabel">Label</label>' +
                '<div class="custom-control custom-checkbox" style="position: absolute; top: 92px; right: 3.5em;">' +
                '    <style>' +
                '        .file-upload-checkbox-label::before, .file-upload-checkbox-label::after {left: 6.5rem; top: 1px;}' +
                '    </style>' +
                '    <input type="checkbox" class="custom-control-input" id="auxFileUploadCheckbox">' +
                '    <label class="custom-control-label text-primary file-upload-checkbox-label" style="line-height: 1.5em; font-size: 1rem; font-weight: 600;" for="auxFileUploadCheckbox">Auxiliary File</label>' +
                '</div>' +
                '<input name="userLabel" type="text" style="border: 1px solid #ced4da; margin: 0; border-radius: 0; font-family: Oxygen, sans-serif; font-weight: 600; font-size: 0.80rem;" maxlength="40" aria-label="Label" placeholder="Concise label (e.g., Meal, Laptop, etc.)" required>' +
                '<label for="userDescription">Description</label>' +
                '<textarea name="userDescription" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" rows="10" placeholder="Provide a brief summary explaining the charges and any special notes…" required></textarea>' +
                '<label class="file-upload-value-group" for="dollars">Dollar Amount (USD)</label>' +
                '<div class="input-group file-upload-value-group">' +
                '    <div class="input-group-prepend" style="max-width: 4% !important;">' +
                '        <span class="input-group-text" style="font-weight: 800; border-radius: 0;"><i class="fas fa-dollar-sign mx-2"></i></span>' +
                '    </div>' +
                '    <input name="dollarAmount" type="number" class="form-control file-upload-value-input" style="max-width: 80% !important; border: 1px solid #ced4da; margin: 0; border-radius: 0; text-align: right;" max="9007199254740991" min="0" aria-label="Dollars" pattern="[0-9]{13}" inputmode="numeric" required>' +
                '    <div class="input-group-append" style="max-width: 4% !important;">' +
                '        <span class="input-group-text mx-2" style="font-weight: 800; border-left: none;border-right: none;">.</span>' +
                '    </div>' +
                '    <input name="centAmount" type="number" class="form-control file-upload-value-input" style="max-width: 12% !important; border: 1px solid #ced4da; margin: 0; border-radius: 0;" max="99" min="0" aria-label="Cents" pattern="[0-9]{2}" inputmode="numeric" required>' +
                '</div>' +
                '<p><span class="badge badge-dark">' + fName + '</span></p>'
            ].join(''),
            buttons: [
                $.extend({}, vex.dialog.buttons.YES, { text: "SUBMIT" }),
                $.extend({}, vex.dialog.buttons.NO, { text: "CANCEL" })
            ],
            afterOpen: function(e) {
                console.log(e);
                $("#auxFileUploadCheckbox").change(function(e) {
                    let file_value_inputs = $(".file-upload-value-input");

                    if (this.checked) {
                        $(".file-upload-value-group").hide();
                        file_value_inputs.prop('required', false);
                        file_value_inputs.prop('disabled', true);
                    }
                    else {
                        $(".file-upload-value-group").show();
                        file_value_inputs.prop('required', true);
                        file_value_inputs.prop('disabled', false);
                    }
                });
            },
            callback: function(data) {
                if (data) {
                    file.userDescription = data.userDescription.trim();
                    file.dollarAmount = data.dollarAmount !== undefined ? parseFloat((data.dollarAmount.trim() ? data.dollarAmount.trim() : 0) + "." + (data.centAmount.trim() ? data.centAmount.trim() : 0)) : 0.0;
                    file.userLabel = data.userLabel.trim();
                    file_details[file.upload.filename] = {"user_description": file.userDescription, "user_label": file.userLabel, "dollar_amount": file.dollarAmount};
                    current_total.text((parseFloat(current_total.text()) + file.dollarAmount).toFixed(2));
                    done();
                } else {
                    done("Upload Cancelled");
                }
            }
        });
    }
};

$(document).ready(function () {
    let request_delete_btn = $(".request-delete-btn");
    let request_void_btn = $(".request-void-btn");
    let request_process_btn = $(".request-process-btn");
    let request_return_btn = $(".request-return-btn");
    let request_edit_btn = $(".edit-request");
    let view_request_history_btn = $(".view-request-history");
    let download_request_pdf = $(".download-request-pdf");
    let download_request = $(".download-request");
    let download_file = $(".download-file");
    let confirm_delete_container = $(".confirm-delete");
    let new_request = window.location.pathname.indexOf("/new/") > -1;
    let edit_request = window.location.pathname.indexOf("/edit/") > -1;

    $('.ui.accordion').accordion();
    $('.ui.dropdown').dropdown();
    request_delete_btn.popup({position: "bottom center", html: "<b>Delete</b>", variation: "tiny"});
    request_void_btn.popup({position: "bottom center", html: "<b>Void</b>", variation: "tiny"});
    $.each(request_process_btn, function(i, e) {
        e = $(e);

        if ($(e.get(0).firstChild).hasClass("fa-check-square")) {
            e.popup({position: "bottom center", html: "<b>Unprocess Request</b>", variation: "tiny"});
        }
        else {
            e.popup({position: "bottom center", html: "<b>Process Request</b>", variation: "tiny"});
        }
    });
    request_return_btn.popup({position: "bottom center", html: "<b>Return Request</b>", variation: "tiny"});
    request_edit_btn.popup({position: "bottom center", html: "<b>Edit Request</b>", variation: "tiny"});
    view_request_history_btn.popup({position: "bottom center", html: "<b>View History</b>", variation: "tiny"});
    download_request_pdf.popup({position: "bottom center", html: "<b>Download PDF Summary</b>", variation: "tiny"});
    download_request.popup({position: "bottom center", html: "<b>Download Submission</b>", variation: "tiny"});
    download_file.popup({position: "bottom center", html: "<b>Download File</b>", variation: "tiny"});

    if (new_request || edit_request) {
        if(new_request) {
            saveOrSubmit(true);
        }

        setInterval(requestTotalSanityCheck, 10000);
        setInterval(function(){saveOrSubmit(true);}, 60000);
    }
    
    $(document).click(function(e) {
        let hide_on_mouseup = [confirm_delete_container];

        $.each(hide_on_mouseup, function (index, itemSet) {
            $.each(itemSet.filter(".visible").add(itemSet.filter(".in")), function(_index, item) {
                item = $(item);

                if (!item.is(e.target) && item.has(e.target).length === 0) {
                    item.transition('vertical flip');
                }
            });
        });
    });

    $("#travel-from").keyup(function() {
        console.log($(this).val().trim());
        $.ajax({
            type: 'GET',
            contentType: 'application/json;charset=UTF-8',
            url: "../../../api/search/places/city/" + $(this).val().trim(),
            dataType: "json",
            success: function (data) {
                //
            }
        });
    });

    $("#request-info input, #request-info textarea").focus(function() {
        if (!$(this).hasClass("datepicker")) {
            $(this).attr("autocomplete", "none");
        }
        else {
            $(this).attr("autocomplete", "off");
        }
    });

    $(".search-requests-form input").focus(function() {
        $(this).attr("autocomplete", "off");
    });

    $("#delete-request").click(function(e) {
        vex.dialog.open({
            message: "Cancel Request?",
            input: "<div style='text-align: center;'><h3>All your changes and the request itself will be lost.</h3></div>",
            buttons: [
                $.extend({}, vex.dialog.buttons.YES, { text: "YES" }),
                $.extend({}, vex.dialog.buttons.NO, { text: "NO" })
            ],
            callback: function(data) {
                if (data) {
                    e.preventDefault();
                    cancelRequest(false, true);
                    window.onbeforeunload = null;
                    document.location.href = "../../";
                }
            }
        });
    });

    request_form.submit(function (e) {
        e.preventDefault();
        window.onbeforeunload = undefined;

        if ($.isEmptyObject(file_selector_map)) {
            toastr["warning"]("You must upload at least one file (e.g., invoice, receipt, etc.).");

            return false;
        }

        vex.dialog.open({
            message: "Submit Request?",
            input: '<div style="text-align: center;"><small>You won\'t be able to further edit this request.</small></div>' +
                '<label for="userMessage">Message</label>' +
                '<textarea name="userMessage" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" rows="10" aria-label="Message" placeholder="Optional message to include in the submission e-mail…"></textarea>',
            buttons: [
                $.extend({}, vex.dialog.buttons.YES, { text: "YES" }),
                $.extend({}, vex.dialog.buttons.NO, { text: "NO" })
            ],
            callback: function(data) {
                if (data) {
                    saveOrSubmit(false, (data.userMessage !== undefined ? data.userMessage: ""));
                }
            }
        });
    });

    $("#requests-advanced-search-btn").click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let advanced_search_div = $('#request-advanced-search');
        let outer_scope_this = $(this);

        if (!advanced_search_div.hasClass("animating")) {
            advanced_search_div.transition({
                animation:"scale",
                duration: "75ms",
                onStart: function(e) {
                    if (advanced_search_div.hasClass("in")) {
                        outer_scope_this.html("Close Advanced Search  <i class=\"fas fa-level-up-alt\"></i>");
                    }
                    else {
                        outer_scope_this.html("Open Advanced Search  <i class=\"fas fa-level-down-alt\"></i>");
                    }
                }
            });
        }
    });

    view_request_history_btn.click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        $($(this).find("svg").attr("data-target")).modal("show");
    });

    download_request.click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let details_container = getNthParent($(this), 3).siblings("div.request-div");
        
        downloadHelper(details_container, false, null);
        toastr["info"]("Gathering files. Download will begin shortly.");

        return false;
    });

    download_request_pdf.click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let details_container = getNthParent($(this), 3).siblings("div.request-div");
        
        downloadHelper(details_container, true, null);
        toastr["info"]("Generating PDF Summary. Download will begin shortly.");

        return false;
    });

    download_file.click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        let details_container = $(getNthParent($(this), 7)).siblings();

        downloadHelper(details_container, false, $(this).attr("file-name"));

        return false;
    });
    

    request_edit_btn.click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let details_container = getNthParent($(this), 3).siblings("div.request-div");

        document.location.href = "../../edit/request/?user_id=" + details_container.find("#requester-net-id").text() +
                                 "&request_id=" + details_container.find("#request-id").text();
    });

    preventInput(pay_to_selected.find("input"));

    $("#no-id-switch").change(function(e) {
        if (this.checked) {
            pay_to_cse.hide();
            pay_to_selected.find("input").prop('required', false);
            pay_to_cse.find("input").prop('disabled', true);
            pay_to_cse.find("input").val("");
            payee_name = "";
            pay_to_noncse.find("input").prop('disabled', false);
            pay_to_noncse.find("input").prop('required', true);
            pay_to_noncse.show();
        }
        else {
            pay_to_noncse.hide();
            pay_to_noncse.find("input").prop('required', false);
            pay_to_noncse.find("input").prop('disabled', true);
            pay_to_noncse.find("input").val("");
            pay_to_cse.find("input").prop('disabled', false);
            pay_to_selected.find("input").prop('required', true);
            pay_to_cse.show();

        }

    });

    $("#request-type").change(function (e) {
        if ($(this).val() === "General") {
            travel_request_inputs.prop('disabled', true);
            travel_request_inputs.prop('required', false);
            travel_request_inputs.val("");
            $("#ctp-receipts-provided-checkbox").prop('checked', false);
            travel_request_div.hide();
        }
        else {
            travel_request_inputs.prop('disabled', false);
            travel_request_inputs.prop('required', true);
            travel_request_div.css('display', 'flex');
        }
    });


    request_process_btn.click(function(e) {
        let request_container_link = getNthParent($(this), 3).siblings("div.request-div").find("a");
        let request_return_button_div = getNthParent($(this), 2).find("button.request-return-btn").parent();
        let request_void_button_div = getNthParent($(this), 2).find("button.request-void-btn").parent();
        let is_checked = toggleProcessRequest(this);

        request_process_btn.popup("hide");
        processRequest(
            request_container_link.find("#requester-net-id").text(),
            request_container_link.find("#request-id").text(),
            is_checked, this, request_return_button_div, request_void_button_div
        );
    });

    request_delete_btn.click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let confirm_delete = getNthParent($(this), 3).siblings("div.request-div").find(".confirm-delete");

        if (!confirm_delete.hasClass("animating")) {
            confirm_delete.transition('vertical flip');
        }
    });

    $(".confirm-request-delete").click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let confirm_delete = getNthParent($(this), 4);
        let request_container = getNthParent($(this), 6);

        if (!confirm_delete.hasClass("animating")) {
            let folder_name = request_container.find("#request-id").text();

            $.ajax({
                type: 'DELETE',
                contentType: 'application/json;charset=UTF-8',
                data: JSON.stringify({
                    user_id: null,
                    folder_name: folder_name,
                    delete_request: true
                }, null, "\t"),
                url: "../../",
                dataType: "json",
                success: function (data) {
                    request_container.remove();
                    toastr[data.type](data.message);
                }
            });
        }
    });

    $(".deny-request-delete").click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let confirm_delete = getNthParent($(this), 4);

        if (!confirm_delete.hasClass("animating")) {
            confirm_delete.transition('vertical flip');
        }
    });

    request_void_btn.click(function(e) {
        e.preventDefault();
        e.stopPropagation();
        let request_div = getNthParent($(this), 3).siblings("div.request-div");
        let is_processed = request_div.attr("data-request-processed");
        let request_container_link = request_div.find("a");
        let request_controls = getNthParent($(this), 3).find("div.request-pr-rt-v-controls");

        if(current_user.user_roles.STFADM || is_processed === "false") {
            vex.dialog.open({
                message: "Void Request",
                input: [
                    '<label for="returnMessage">Message</label>' +
                    '<textarea name="returnMessage" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" rows="10" aria-label="Message" placeholder="Reason for voiding the request…" required></textarea>' +
                    '<p class="text-danger fw-800 font-italic">This process is irreversible.</p>'
                ].join(''),
                buttons: [
                    $.extend({}, vex.dialog.buttons.YES, { text: "VOID" }),
                    $.extend({}, vex.dialog.buttons.NO, { text: "CANCEL" })
                ],
                callback: function(data) {
                    if (data) {
                        $.ajax({
                            type: 'POST',
                            contentType: 'application/json;charset=UTF-8',
                            data: JSON.stringify({return_message: data.returnMessage,
                                                  request_id: request_container_link.find("#request-id").text(),
                                                  net_id: request_container_link.find("#requester-net-id").text()
                                                 }, null, "\t"),
                            url: "../../void/request/",
                            dataType: "json",
                            success: function (data) {
                                if(data.success) {
                                    request_controls.remove();
                                    $.each(["uta-orange-bg", "bg-dark", "uta-blue-bg", "request-returned"], function(index, value) {
                                        request_container_link.removeClass(value);
                                    });
                                    request_container_link.addClass("bg-secondary");
                                    request_container_link.addClass("border-secondary");
                                    request_container_link.prepend('<div class="request-void-text">VOID</div>');
                                }

                                toastr[data.type](data.message);
                            }
                        });
                    }
                }
            });
        }
        else {
            toastr["error"]("Processed requests cannot be voided by the requester.");
        }
    });

    request_return_btn.click(function () {
        let request_container_link = getNthParent($(this), 3).siblings("div.request-div").find("a");
        let request_container = getNthParent($(this), 4);

        if (getNthParent($(this), 3).siblings("div.request-div").attr("data-request-processed") === "false") {
            request_return_btn.popup("hide");
            vex.dialog.open({
                message: "Return Request to User",
                input: [
                    '<label for="returnMessage">Message</label>' +
                    '<textarea name="returnMessage" style="border: 1px solid #ced4da; margin: 0; border-radius: 0;" rows="10" aria-label="Message" placeholder="Reason for returning the request…" required></textarea>'
                ].join(''),
                buttons: [
                    $.extend({}, vex.dialog.buttons.YES, { text: "RETURN" }),
                    $.extend({}, vex.dialog.buttons.NO, { text: "CANCEL" })
                ],
                callback: function(data) {
                    if (data) {
                        $.ajax({
                            type: 'POST',
                            contentType: 'application/json;charset=UTF-8',
                            data: JSON.stringify({return_message: data.returnMessage,
                                                  request_id: request_container_link.find("#request-id").text(),
                                                  net_id: request_container_link.find("#requester-net-id").text()
                                                 }, null, "\t"),
                            url: "../../return/request/",
                            dataType: "json",
                            success: function (data) {
                                if (data.success) {
                                    request_container.remove();

                                    if ($("div.row.accordion").length < 1) {
                                        let gui_elements = $("div.container.list-group").has("form").find("div.row");

                                        gui_elements.first().remove();
                                        gui_elements.last().remove();
                                    }
                                }
                                toastr[data.type](data.message);
                            }
                        });
                    }
                }
            });
        }
        else {
            toastr["error"]("You must unprocess a request before returning it.");
        }
    });

    pay_to_cse.search({
        minCharacters : 2,
        selectFirstResult: true,
        searchDelay: 50,
        showNoResults: true,
        maxResults: 15,
        apiSettings: {
            onResponse: function(APIResponse) {
                let response = {
                    results : []
                };

                $.each(APIResponse, function(index, item) {
                    if (item.uta_id.trim()) {
                        response.results.push({
                            title: ((item.first_name != null ? item.first_name: "") + (item.middle_name != null ? " " + item.middle_name + " ": " ") + (item.last_name != null ? item.last_name: "")).replace("   ", " "),
                            description: item.uta_id,
                            email: item.email
                        });
                    }
                });

                return response;
            },
            url: '../../../api/search/user/name/and/net_id/and/uta_id/{query}'
        },
        onSelect: function(selection, APIResponse) {
            $("#request-payto").val(selection.description);
            payee_name = selection.title;
            payee_email = selection.email;

            return true;
        },
    });

    travel_from.search({
        minCharacters : 2,
        selectFirstResult: true,
        searchDelay: 50,
        showNoResults: true,
        maxResults: 8,
        apiSettings: {
            onResponse: function(APIResponse) {
                let response = {
                    results : []
                };

                $.each(APIResponse, function(index, item) {
                    if (index < 7) {
                        response.results.push({
                            title: item.city + ", " + item.state,
                            description: item.country,
                            full_location: {city: item.city, state: item.state, country: item.country}
                        });
                    }
                });

                response.results.push({
                    title: "Powered By",
                    description: "Algolia Places",
                    url: "https://www.algolia.com/places"
                });

                return response;
            },
            url: "../../../api/search/places/city/{query}"
        },
    });

    travel_to.search({
        minCharacters : 2,
        selectFirstResult: true,
        searchDelay: 50,
        showNoResults: true,
        maxResults: 8,
        apiSettings: {
            onResponse: function(APIResponse) {
                let response = {
                    results : []
                };

                $.each(APIResponse, function(index, item) {
                    if (index < 7) {
                        response.results.push({
                            title: item.city + ", " + item.state,
                            description: item.country,
                            full_location: {city: item.city, state: item.state, country: item.country}
                        });
                    }
                });

                response.results.push({
                    title: "Powered By",
                    description: "Algolia Places",
                    url: "https://www.algolia.com/places"
                });

                return response;
            },
            url: "../../../api/search/places/city/{query}"
        },
    });
});
