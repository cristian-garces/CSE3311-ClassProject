const toast_types = ["success", "info", "warning", "error"];

toastr.options = {
    "closeButton": false,
    "debug": false,
    "newestOnTop": false,
    "progressBar": true,
    "positionClass": "toast-bottom-center",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": "150",
    "hideDuration": "150",
    "timeOut": "2500",
    "extendedTimeOut": "1500",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

function contactWebmaster() {
    window.location.href = decryptMail("nbjmup;xfcnbtufs.dtfAvub/fev");
    return true
}

function preventInput(input_field, input_actions=null) {
    input_actions = input_actions ? input_actions : "keydown paste cut dragenter dragover drop";

    input_field.on(input_actions, function(e) {
        e.preventDefault();
    });
}

function getNthParent(e, n) {
    let nthParent = e;

    for(let i = 1; i <= n; i++) {
        nthParent = nthParent.parent();
    }
    return nthParent
}

$('.contact-webmaster').click(function(e) {
    e.preventDefault();
    return contactWebmaster();
});

$(".update-char").keyup(function() {
    let chars_left = parseInt($(this).attr("maxlength"))-parseInt($(this).val().length);
    getNthParent($(this), 2).find(".char-count").text(chars_left);
});

function decryptMail(s)  {
    let n = 0;
    let r = "";

    for (let i = 0; i < s.length; i++) {
        n = s.charCodeAt(i);
        if (n >= 8364) {
            n = 128;
        }
        r += String.fromCharCode(n - 1);
    }

    return r;
}

$(document).ready(function () {
 // Place holder for future development
});