var app_version = navigator.appVersion.toLowerCase ();
var user_agent = navigator.userAgent.toLowerCase ();
var detected_os = "unknown";

function detect_os (ua_fragment, output_os)
{
    var fingerprint = ua_fragment.toLowerCase ();
    if (app_version.indexOf (fingerprint) >= 0 || user_agent.indexOf (fingerprint) >= 0) {
        detected_os = output_os;
    }
}

detect_os ("Mac", "OSX");
detect_os ("Win", "Win");
detect_os ("openSUSE", "Linux");
detect_os ("SUSE", "Linux");
detect_os ("SLED", "Linux");
detect_os ("Ubuntu", "Linux");
detect_os ("Debian", "Linux");
detect_os ("Fedora", "Linux");
detect_os ("RedHat", "Linux");
detect_os ("Foresight", "Linux");

var default_distro = detected_os.toLowerCase ();

var href_parts = document.location.href.split ('#');
if (href_parts.length > 1) {
    var override_distro = href_parts[href_parts.length - 1].toLowerCase ();
    if (override_distro.length > 1) {
        default_distro = override_distro;
    }
}

function show_distro_details (button)
{
    var title = $$('#' + button.id + ' h4')[0].innerHTML;
    var content = $$('#' + button.id + ' div.details')[0].innerHTML;

    button.addClassName ('chosen');
    $$('#distros div.button').each (function (element, index) {
        if (element != button) {
            element.removeClassName ('chosen');
        }
    });

    $('distro-details').innerHTML = content;
    var header = "Install on " + title;
    if (title == "Source") {
        header = "Install from Source";
    }
    $('distro-details-header').innerHTML = header;
}

function install_distro_button_actions ()
{
    $$('#distros div.button').each (function (button, index) {
        if (button.id == 'distro-' + default_distro) {
            show_distro_details (button);
        }
        button.observe ('click', function () { show_distro_details (button); } );
    });

    $('distro-details').setStyle ("display: block");
}

Event.observe(window, 'load', install_distro_button_actions);

