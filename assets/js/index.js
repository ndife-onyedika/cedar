// ------------------------------------------------------
// TOASTS
// ------------------------------------------------------
const display_toast = toast => {
    let bs_toast = new bootstrap.Toast(toast);
    $(".toast-container").append(toast);
    bs_toast.show();
    $(toast).on("hidden.bs.toast", function () {
        setTimeout(() => $(this).remove(), 200);
    });
};

const toastElList = $(".toast");
const toastList = [...toastElList].forEach(toastEl => display_toast(toastEl));

const toast = (status, message) => {
    status = status.toLowerCase();
    let toast = `
        <div class="toast text-bg-${status == "error" ? "danger" : status}" role="alert"
            aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <svg class="bi me-2" style="fill:var(--bs-${status == "error" ? "danger" : status})">
                    <use xlink:href="/static/svg/sprite.svg#icon-${status}-bold"></use>
                </svg>
                <strong class="me-auto">${capitalize(status)}</strong>
                <small class="text-muted">Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    display_toast($(toast));
};

// ------------------------------------------------------
// SELECT DROPDOWN
// ------------------------------------------------------
function create_custom_dropdowns() {
    $(document)
        .find(".search-select")
        .each(function (i, select) {
            $(this).css("display", "none");
            if (!$(this).next().hasClass("custom_dropdown-select")) {
                $(this).after(
                    `
                        <div class="custom_dropdown-select position-relative" tabindex="0">
                            <span class="current text-truncate w-100 d-block"></span>
                            <div class="card border-0 shadow-sm bg-white rounded-1 position-absolute start-0">
                                <div class="list overflow-auto position-relative">
                                    <ul></ul>
                                </div>
                            </div>
                        </div>
                    `
                );
                var dropdown = $(this).next();
                var options = $(select).find("option");
                var selected = $(this).find("option:selected");
                dropdown.find(".current").html(selected.data("display-text") || selected.text());
                options.each(function (j, o) {
                    var display = $(o).data("display-text") || "";
                    dropdown.find("ul").append(`
                        <li 
                            data-value="${$(o).val()}"
                            data-display-text="${display}"
                            class="option ${$(o).is(":selected") ? "selected" : ""}">
                            ${$(o).text()}
                        </li>
                    `);
                });
            }

            if ($(this).find("option").length > 10)
                $(this).next().find("ul").before(`
                <div class="p-2 position-sticky top-0 bg-white">
                    <input id="txtSearchValue" autocomplete="off" class="dd-searchbox form-control" placeholder="Search..." type="text">
                </div>
            `);

            if ($(this).parent().parent().hasClass("top")) {
                $(this).next().find(".list").css({ top: "-10rem" });
            }
        });
}

// Event listeners

// Open/close
$(document).on("click", ".custom_dropdown-select", function (event) {
    $(".custom_dropdown-select").not($(this)).removeClass("open");
    if (!$(this).hasClass("disabled")) {
        if ($(event.target).hasClass("dd-searchbox")) {
            return;
        }
        $(this).toggleClass("open");
        if ($(this).hasClass("open")) {
            $(this).find(".option").attr("tabindex", 0);
            $(this).find(".selected").focus();

            $(this).find(".dd-searchbox").focus();
        } else {
            $(this).find(".option").removeAttr("tabindex");
            $(this).focus();
        }
    }
});

// Close when clicking outside
$(document).on("click", function (event) {
    if ($(event.target).closest(".custom_dropdown-select").length === 0) {
        $(".custom_dropdown-select").removeClass("open");
        $(".custom_dropdown-select .option").removeAttr("tabindex");
    }
    event.stopPropagation();
});

// Search
$(document).on("input", ".dd-searchbox", function () {
    var self = $(this);
    var valThis = self.val();
    self.parent()
        .parent()
        .find("ul")
        .find("li")
        .each(function () {
            var text = $(this).text();
            text.toLowerCase().indexOf(valThis.toLowerCase()) > -1 ? $(this).show() : $(this).hide();
        });
});

// Option click
$(document).on("click", ".custom_dropdown-select .option", function (event) {
    $(this).closest(".list").find(".selected").removeClass("selected");
    $(this).addClass("selected");
    var text = $(this).data("display-text") || $(this).text();
    $(this).closest(".custom_dropdown-select").find(".current").text(text);
    $(this).closest(".custom_dropdown-select").prev("select").val($(this).data("value")).trigger("change");
});

// Keyboard events
$(document).on("keydown", ".custom_dropdown-select", function (event) {
    var focused_option = $($(this).find(".list .option:focus")[0] || $(this).find(".list .option.selected")[0]);
    // Space or Enter
    //if (event.keyCode == 32 || event.keyCode == 13) {
    if (event.keyCode == 13) {
        if ($(this).hasClass("open")) {
            focused_option.trigger("click");
        } else {
            $(this).trigger("click");
        }
        return false;
        // Down
    } else if (event.keyCode == 40) {
        if (!$(this).hasClass("open")) {
            $(this).trigger("click");
        } else {
            focused_option.next().focus();
        }
        return false;
        // Up
    } else if (event.keyCode == 38) {
        if (!$(this).hasClass("open")) {
            $(this).trigger("click");
        } else {
            var focused_option = $($(this).find(".list .option:focus")[0] || $(this).find(".list .option.selected")[0]);
            focused_option.prev().focus();
        }
        return false;
        // Esc
    } else if (event.keyCode == 27) {
        if ($(this).hasClass("open")) {
            $(this).trigger("click");
        }
        return false;
    }
});

$(document).ready(function () {
    create_custom_dropdowns();
});
