$(document).ready(function () {
    let ret_url = getUrlParameter("next") || root_path;
    let password_input = $("#password");

    $("#show-pass, #show-pass > svg").click(function () {
        let show_pass_checkmark = $("#show-pass");

        if (password_input.attr("type") === "password") {
            show_pass_checkmark.html('Password <i class="fas fa-eye-slash ml-2"></i>');
            password_input.attr('type', 'text');
        }
        else {
            show_pass_checkmark.html('Password <i class="fas fa-eye ml-2"></i>');
            password_input.attr('type', 'password');
        }
    });

    $("#login-form").submit(function (e) {
        e.preventDefault();
        let pathName = $(window.location)[0].pathname;

        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({netid: $("#netid").val(), password: $("#password").val(), next: ret_url}, null, "\t"),
            url: pathName,
            dataType: "json",
            success: function (data) {
                if (data.error) {
                    toastr[data.type](data.message);
                }
                else {
                    document.location.href = data.return_url;
                }
            }
        });
    });
});
