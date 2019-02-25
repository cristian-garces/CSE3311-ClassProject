const toast_types = ["success", "info", "warning", "error"];
const weekday_map = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"};
const back_to_top = $('#back-to-top');
let date_pickers = {};
let add_row_btn = $("#add-row-btn");
let row_to_clone =  $("#clonable-row").clone();
let remove_labels = true;
row_to_clone.last().append('<button class="remove-row-btn text-danger"><i class="fas fa-minus-circle"></i></button>');
vex.defaultOptions.className = 'vex-theme-flat-attack';

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

// https://github.com/saltycrane/session-timeout-example
sessionMonitor = function(options) {
    "use strict";
    let defaults = {
            sessionLifetime: 30 * 60 * 1000,
            timeBeforeWarning: 5 * 60 * 1000,
            minPingInterval: 60 * 1000,
            activityEvents: 'mouseup',
            pingUrl: '/ping',
            timeoutRedirectUrl: '/login',
            ping: function () {
                $.ajax({
                    type: 'POST',
                    url: self.pingUrl,
                    success: function (data) {
                        if (data === "logged_out") {
                            document.location.href = self.timeoutRedirectUrl;
                        }
                    }
                });
            },
            logout: function () {
                logoutUser();
            },
            onwarning: function () {
                let warningMinutes = Math.round(self.timeBeforeWarning / 60 / 1000),
                    $alert = $('<div id="jqsm-warning">Your session will expire in ' + warningMinutes + ' minutes. ' +
                              '<button id="jqsm-stay-logged-in">Stay Logged In</button>' +
                              '<button id="jqsm-log-out">Log Out</button>' +
                              '</div>');
                let body = $('body');

                if (!body.children('div#jqsm-warning').length) {
                    body.prepend($alert);
                }

                $('div#jqsm-warning').show();

                $('button#jqsm-stay-logged-in').on('click', self.extendsess).on('click',
                    function () {
                        $alert.hide();
                    }
                );

                $('button#jqsm-log-out').on('click', self.logout);
            },
            onbeforetimeout: function () {
            },
            ontimeout: function () {
                logoutUser(self.timeoutRedirectUrl)
            }
        },
        self = {},
        _warningTimeoutID,
        _expirationTimeoutID,
        _lastPingTime = 0;

    function extendsess () {
        let now = $.now(),
            timeSinceLastPing = now - _lastPingTime;

        if (timeSinceLastPing > self.minPingInterval) {
            _lastPingTime = now;
            _resetTimers();
            self.ping();
        }
    }

    function _resetTimers () {
        let warningTimeout = self.sessionLifetime - self.timeBeforeWarning;

        window.clearTimeout(_warningTimeoutID);
        window.clearTimeout(_expirationTimeoutID);
        _warningTimeoutID = window.setTimeout(self.onwarning, warningTimeout);
        _expirationTimeoutID = window.setTimeout(_onTimeout, self.sessionLifetime);
    }

    function _onTimeout () {
        $.when(self.onbeforetimeout()).always(self.ontimeout);
    }

    $.extend(self, defaults, options, {
        extendsess: extendsess
    });

    $(document).on(self.activityEvents, extendsess);
    extendsess();

    return self;
};

// https://stackoverflow.com/a/6189418/1217580
function getClient() {
    let ua = navigator.userAgent;
    let p = navigator.platform;
    let engine = {
        ie: 0,
        edge: 0,
        gecko: 0,
        webkit: 0,
        khtml: 0,
        opera: 0,
        ver: null
    };
    let browser = {
        ie: 0,
        edge: 0,
        firefox: 0,
        safari: 0,
        konq: 0,
        opera: 0,
        chrome: 0,
        ver: null
    };
    let system = {
        win: false,
        mac: false,
        x11: false,
        iphone: false,
        ipod: false,
        nokiaN: false,
        winMobile: false,
        macMobile: false,
        wii: false,
        ps: false
    };

    if (window.opera) {
        engine.ver = browser.ver = window.opera.version();
        engine.opera = browser.opera = parseFloat(engine.ver);
    }
    else if (/Edge\/([^;]+)/.test(ua)) {
        engine.ver = browser.ver = RegExp["$1"];
        engine.edge = browser.edge = parseFloat(engine.ver);
    }
    else if (/AppleWebKit\/(\S+)/.test(ua)) {
        engine.ver = RegExp["$1"];
        engine.webkit = parseFloat(engine.ver);

        if (/Chrome\/(\S+)/.test(ua)) {
            browser.ver = RegExp["$1"];
            browser.chrome = parseFloat(browser.ver);
        }
        else if (/Version\/(\S+)/.test(ua)) {
            browser.ver = RegExp["$1"];
            browser.safari = parseFloat(browser.ver);
        }
        else {
            let safariVersion = 1;

            if (engine.webkit < 100) {
                safariVersion = 1;
            }
            else if (engine.webkit < 312) {
                safariVersion = 1.2;
            }
            else if (engine.webkit < 412) {
                safariVersion = 1.3;
            }
            else {
                safariVersion = 2;
            }

            browser.safari = browser.ver = safariVersion;
        }
    }
    else if (/KHTML\/(\S+)/.test(ua) || /Konqueror\/([^;]+)/.test(ua)) {
        engine.ver = browser.ver = RegExp["$1"];
        engine.khtml = browser.konq = parseFloat(engine.ver);
    }
    else if (/rv:([^)]+)\) Gecko\/\d{8}/.test(ua)) {
        engine.ver = RegExp["$1"];
        engine.gecko = parseFloat(engine.ver);

        if (/Firefox\/(\S+)/.test(ua)) {
            browser.ver = RegExp["$1"];
            browser.firefox = parseFloat(browser.ver);
        }
    }
    else if (/MSIE ([^;]+)/.test(ua)) {
        engine.ver = browser.ver = RegExp["$1"];
        engine.ie = browser.ie = parseFloat(engine.ver);
    }
    else if (/Trident\/([^;]+)/.test(ua)) {
        engine.ver = RegExp["$1"];
        browser.ver = parseFloat(ua.split("rv:")[1]);
        engine.ie = parseFloat(browser.ver);
    }

    browser.ie = engine.ie;
    browser.opera = engine.opera;
    system.win = p.indexOf("Win") === 0;
    system.mac = p.indexOf("Mac") === 0;
    system.x11 = (p === "X11") || (p.indexOf("Linux") === 0);

    if (system.win) {
        if (/Win(?:dows )?([^do]{2})\s?(\d+\.\d+)?/.test(ua)) {
            if (RegExp["$1"] === "NT") {
                switch (RegExp["$2"]) {
                    case "5.0":
                        system.win = "2000";
                        break;
                    case "5.1":
                        system.win = "XP";
                        break;
                    case "6.0":
                        system.win = "Vista";
                        break;
                    default:
                        system.win = "NT";
                        break;
                }
            } else if (RegExp["$1"] === "9x") {
                system.win = "ME";
            } else {
                system.win = RegExp["$1"];
            }
        }
    }

    system.iphone = ua.indexOf("iPhone") > -1;
    system.ipod = ua.indexOf("iPod") > -1;
    system.nokiaN = ua.indexOf("NokiaN") > -1;
    system.winMobile = (system.win === "CE");
    system.macMobile = (system.iphone || system.ipod);
    system.wii = ua.indexOf("Wii") > -1;
    system.ps = /playstation/i.test(ua);

    return {
        engine: engine,
        browser: browser,
        system: system
    }
}

// https://stackoverflow.com/a/21903119
function getUrlParameter(sParam) {
    let sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? null : sParameterName[1];
        }
    }

    return null;
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

function htmlDecode(input) {
    let doc = new DOMParser().parseFromString(input, "text/html");
    
    return doc.documentElement.textContent;
}

function getNthParent(e, n) {
    let nthParent = e;

    for(let i = 1; i <= n; i++) {
        nthParent = nthParent.parent();
    }
    
    return nthParent
}

function createUniqueFolderName() {
    let d = new Date();

    return "[" + (((d.getTime() * (Math.random() + 0.001))/299792458)).toFixed(3) + "]---" +
    + (d.getMonth() + 1) + "." + d.getDate() + "." + d.getFullYear() + "-" + d.getHours() + "." + d.getMinutes() + "."
    + d.getSeconds() + "." + d.getMilliseconds();
}

function getFormattedDate() {
    let d = new Date();

    return String(d.getMonth() + 1).padStart(2, "0") + "/" + String(d.getDate()).padStart(2, "0") + "/" + String(d.getFullYear()).padStart(4, "0")
}

function getFormmatedTime() {
    let d = new Date();

    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0") + ":" + String(d.getSeconds()).padStart(2, "0") + "." + String(d.getMilliseconds()).padStart(3, "0")
}

function addRowInit(parent_container, remove_label_elements=null) {
    remove_labels = remove_label_elements != null ? remove_label_elements : true;
    parent_container.hover(
        function() {
            let btn_position = $(add_row_btn).parent().position();

            $(add_row_btn).css({
                "top": (btn_position.top + 29) + "px",
                "left": (btn_position.left - 50) + "px"
            });

            add_row_btn.finish();
            add_row_btn.fadeIn(500);

        },
        function() {
            let add_row_btn = $("#add-row-btn");
            add_row_btn.finish();
            add_row_btn.fadeOut(500);
        }
    );
}

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

function logoutUser(redirect=null) {
    $.ajax({
        type: 'POST',
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({logout: true}, null, "\t"),
        url: root_path + "logout",
        dataType: "json",
        success: function (data) {
            if (data.success) {
                document.location.href = redirect != null ? redirect : root_path;
            }
        }
    });
}

$(document).ready(function () {
    $(".datepicker").each(function() {
        date_pickers[$(this)] = new Pikaday({
            field: $(this)[0],
            onSelect: function() {
                this.getMoment();
            }
        });
    });
    
    $("#main-site-drawer").sidebar({
        onVisible: function() {
            $("body, #main-layout-container").css("overflow-x", "hidden");
            $("#main-layout-container").css("overflow-y", "hidden");
        }, 
        onHidden: function() {
            $("body, #main-layout-container").css("overflow-x", "auto");
            $("#main-layout-container").css("overflow-y", "auto");
        }
    });

    $("#main-site-drawer-toggle").click(function() {
        $("#main-site-drawer").sidebar("setting", "transition", "push").sidebar("toggle");
    });

    $("#main-site-drawer > a.no-apps").click(function(e) {
        toastr["error"]("You don't have access to any apps. Log in or e-mail <a href=\"#\" class=\"badge badge-light contact-webmaster\" style=\"color: #333333; vertical-align: middle;\">webmaster-cse@uta.edu</a>");
        
        $("#toast-container > .toast > .toast-message").find(".contact-webmaster").click(function (e) {
            e.preventDefault();
            return contactWebmaster();
        });
    });

    $(".logout-btn").click(function (e) {
        logoutUser();
    });

    add_row_btn.click(function(e) {
        e.preventDefault();
        let new_row = row_to_clone.clone();
        if(remove_labels) {
            new_row.find("label").remove();
        }

        $(new_row).find(".datepicker").each(function() {
            date_pickers[$(this)] = new Pikaday({
                field: $(this)[0],
                onSelect: function() {
                    console.log(this.getMoment());
                }
            });
        });

        new_row.appendTo($(this).parent());
    });

    $(document).on('click', '.remove-row-btn', function(e) {
        e.preventDefault();

        $(this).parent().find(".datepicker").each(function() {
            delete date_pickers[$(this)];
        });

        $(this).parent().remove();
    });

    $(".site-wide-search").search({
        minCharacters : 2,
        selectFirstResult: true,
        searchDelay: 50,
        showNoResults: true,
        apiSettings   : {
            onResponse: function(APIResponse) {
                let response = {
                    results : []
                };

                $.each(APIResponse, function(index, item) {
                    response.results.push({
                        title: item.title,
                        description: item.description,
                        url: root_path + item.url
                    });
                });

                return response;
            },
            url: root_path + "api/search/site/{query}"
        }
    });

    if (back_to_top.length) {
        let scrollTrigger = 50;
        let backToTop = function () {
            let scrollTop = Math.max($(window).scrollTop(), window.scrollY, $("body").scrollTop(), $("html").scrollTop());
            let back_to_top = $('#back-to-top');

            if (scrollTop > scrollTrigger) {
                back_to_top.css("display", "block");
                back_to_top.addClass("show");
            } else {
                back_to_top.removeClass("show");
                back_to_top.css("display", "none");
            }
        };

        backToTop();

        $(window).scroll(function() {
            backToTop();
        });

        back_to_top.click(function (e) {
            e.preventDefault();

            $("body, html").animate({
                scrollTop: 0
            }, 450);
        });
    }
});
