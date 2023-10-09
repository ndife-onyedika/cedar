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
    let isPrompt = status == "prompt";
    // let toast = `
    //     <div class="toast text-bg-${status == "error" ? "danger" : status}" role="alert"
    //         aria-live="assertive" aria-atomic="true">
    //         <div class="toast-header">
    //             <svg class="bi me-2" style="fill:var(--bs-${status == "error" ? "danger" : status})">
    //                 <use xlink:href="/static/svg/sprite.svg#icon-${status}-bold"></use>
    //             </svg>
    //             <strong class="me-auto">${capitalize(status)}</strong>
    //             <small class="text-muted">Just now</small>
    //             <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
    //         </div>
    //         <div class="toast-body">
    //             ${message}
    //         </div>
    //     </div>
    // `;
    let toast = `
        <div class="toast border-0 ${isPrompt ? "align-items-center text-bg-light" : `text-bg-${status == "error" ? "danger" : status}`}" role="alert"
            aria-live="assertive" aria-atomic="true">
            <div class="toast-body p-4 fw-bold hstack gap-2 align-items-start">
                <svg class="bi" style="fill:currentColor;width:1.2rem;height:1.2rem">
                    <use xlink:href="/static/svg/sprite.svg#icon-${isPrompt ? "info" : status}-bold"></use>
                </svg>
                <span class="d-inline-block" style="flex:1;">${message}</span>
            </div>
        </div>
    `;
    display_toast($(toast));
};
// ------------------------------------------------------
// PROMPT MODAL
// ------------------------------------------------------
const display_prompt = modal => {
    const promptModalElList = $(".modal#cm, .modal-backdrop");
    const promptModalList = [...promptModalElList].forEach(promptEl => $(promptEl).remove());
    let bs_prompt = new bootstrap.Modal(modal);
    bs_prompt.show();
};
const promptModal = (status, message, func) => {
    status = status.toLowerCase();
    let modal = `
        <div class="modal fade" id="cm" tabindex="-1" aria-labelledby="cml" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable vstack gap-2 justify-content-center">
                <button type="button"
                    style="background-color:#fff;width:unset;height:unset;background-size:.6rem;padding:.9rem"
                    class="btn-close rounded-circle ms-auto" data-bs-dismiss="modal"
                    aria-label="Close"></button>
                <div class="modal-content rounded-4 border-0" style="max-height: 100%;">
                    <div class="modal-header border-bottom-0 position-relative">
                        <h1 class="modal-title fs-5" id="cml"></h1>
                    </div>
                    <div class="modal-body overflow-auto text-center">
                        <h5 class="fw-bold">${capitalize(status)}</h5>
                        <p class="mb-0">${message}</p>
                    </div>
                    <div class="modal-footer  border-top-0">
                        <button type="button" class="btn btn-light bg-white border-0" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary px-3" ${func ? `onclick="${func}"` : "data-bs-dismiss='modal'"}>Ok</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    display_prompt($(modal));
};

// ------------------------------------------------------
// Show Password
// ------------------------------------------------------
$("#passShow").on("click", function () {
    if (!$(this).hasClass("toggle")) {
        $(this).addClass("toggle");
        $(this).find("use").attr("xlink:href", "/static/svg/sprite.svg#icon-eye-close-outline");
        $(this).prev().find("input").attr("type", "text");
        $(this).prev().focus();
    } else {
        $(this).removeClass("toggle");
        $(this).find("use").attr("xlink:href", "/static/svg/sprite.svg#icon-eye-open-outline");
        $(this).prev().find("input").attr("type", "password");
        $(this).prev().find("input").focus();
    }
});

// ------------------------------------------------------
// SELECT DROPDOWN
// ------------------------------------------------------
const setSelectCurrent = ({ select, ...kwargs }) => {
    if (!select.nextElementSibling.hasAttribute("multiple")) {
        if (kwargs.context == "click") {
            let text = kwargs.selected.getAttribute("data-text") || kwargs.selected.innerText;
            kwargs.selected.closest("ul").querySelector(".active").classList.remove("active");
            kwargs.selected.classList.add("active");

            select.querySelector(".current").innerText = text.trim();
            select.nextElementSibling.value = kwargs.selected.getAttribute("data-value");
            select.nextElementSibling.dispatchEvent(new Event("change", { bubbles: true }));
        }
    } else {
        var text = [];
        var selected = [];
        let current_display = "Choose one";
        select.querySelectorAll("input[type='checkbox']").forEach(checkbox => {
            if (checkbox.checked) {
                selected.push(checkbox.value);
                text.push({ id: checkbox.value, text: checkbox.nextElementSibling.innerText });
                checkbox.closest(".dropdown-item").classList.add("active", "select-active");
                select.nextElementSibling.querySelector(`option[value="${checkbox.value}"]`).selected = true;
            } else {
                checkbox.closest(".dropdown-item").classList.remove("active", "select-active");
                select.nextElementSibling.querySelector(`option[value="${checkbox.value}"]`).selected = false;
            }
        });

        if (text.length > 0) {
            current_display = "";
            text.forEach(item => {
                current_display += `
                    <span class="bg-light rounded-pill py-1 pe-1 ps-2 small hstack gap-1">
                        <span>${item.text}</span>
                        <button 
                            type="button" 
                            aria-label="Close" 
                            data-id="${item.id}"
                            class="p-0 d-flex align-items-center justify-content-center rounded-circle border-0 bg-secondary">
                            <svg style="fill:#fff;width:18px" xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 24 24" width="24" fill="currentColor"><path d="M7.314 5.9l3.535-3.536A1 1 0 1 0 9.435.95L5.899 4.485 2.364.95A1 1 0 1 0 .95 2.364l3.535 3.535L.95 9.435a1 1 0 1 0 1.414 1.414l3.535-3.535 3.536 3.535a1 1 0 1 0 1.414-1.414L7.314 5.899z"></path></svg>
                        </button>
                    </span>
                `;
            });
        }
        select.querySelector(".current").innerHTML = current_display;
    }
};
function create_custom_dropdowns() {
    $(document)
        .find("select.search-select")
        .each(function (i, select) {
            if ($(this).prev().hasClass("custom_dropdown-select") || !$(this).prev().hasClass("custom_dropdown-select")) {
                if ($(this).prev().hasClass("custom_dropdown-select")) $(this).prev().remove();

                let btnClass = $(this).attr("data-class") ?? "";
                let isLarge = $(select).hasClass("search-select-large");
                let selectClass = $(this).attr("class").replace("search-select", "");

                $(this).before(
                    `<div ${isLarge ? "style='--bs-border-color:#ced4da'" : ""} class="custom_dropdown-select position-relative ${
                        selectClass ?? ""
                    }" tabindex="0">
                        <button 
                            type="button"
                            aria-expanded="false"
                            ${$(this).attr("disabled") ? "disabled" : ""}
                            ${$(this).attr("readonly") ? "readonly" : ""}
                            style="cursor:not-allowed;--bs-btn-active-border-color:#8cc3aa"
                            class="current btn btn-lg text-truncate form-select text-dark ${
                                (btnClass ?? "") +
                                (isLarge ? " d-flex gap-1 flex-wrap" : "") +
                                (selectClass.includes("is-invalid") ? " is-invalid border-danger" : "")
                            }">
                                <span class="spinner-border spinner-border-sm spinner-border-slim me-1" role="status" aria-hidden="true"></span>
                                Fetching data...
                            </button>
                            <ul class="dropdown-menu overflow-auto ${
                                ($(this).hasClass("currency") ? "w-auto " : "w-100 ") + ($(this).attr("data-menu-class") ?? "")
                            }" style="max-height:15rem"></ul>
                    </div>`
                );

                var dropdown = $(this).prev();
                var options = $(select).find("option");
                var selected = $(this).find("option:selected");

                if (options.length) {
                    dropdown.find(".current").css("cursor", "pointer");
                    dropdown.find(".current").addClass("dropdown-toggle");
                    dropdown.find(".current").html(selected.text() || "Choose one");
                    dropdown
                        .find(".current")
                        .attr({ "data-bs-toggle": "dropdown", "data-bs-auto-close": !$(select).hasAttr("multiple") ? "true" : "outside" });
                    options.each(function (j, o) {
                        var display = $(o).data("display-text") || "";
                        dropdown.find("ul").append(
                            `<li>
                                ${
                                    !$(select).hasAttr("multiple")
                                        ? `<button 
                                            type="button"
                                            data-value="${$(o).val()}"
                                            style="white-space:normal"
                                            data-display-text="${display}"
                                            class="dropdown-item ${$(o).is(":selected") ? "active" : ""}">
                                            ${$(o).text()}
                                        </button>`
                                        : `<label 
                                            for="${select.name}${j}"
                                            data-value="${$(o).val()}"
                                            style="white-space:normal;"
                                            data-display-text="${display}"
                                            class="dropdown-item hstack gap-2 align-items-center py-2 ${
                                                $(o).is(":selected") ? "active select-active" : ""
                                            }">
                                            <input 
                                                type="checkbox" 
                                                value="${$(o).val()}"
                                                id="${select.name}${j}"
                                                ${$(o).is(":selected") ? "checked" : ""}
                                                class="form-check-input p-0 dropdown-check" />

                                                <span class="lh-1">${$(o).text()}</span>
                                        </label>`
                                }
                            </li>`
                        );
                    });

                    setSelectCurrent({ context: "create", select: select.previousElementSibling });
                }
            }

            if ($(this).find("option").length > 10) {
                $(this).prev().find("ul").addClass("pt-0");
                $(this).prev().find("ul>li:first-child").before(`
                    <div class="p-2 pt-3 position-sticky top-0 bg-white">
                        <input id="txtSearchValue" autocomplete="off" class="dd-searchbox form-control" placeholder="Search..." type="text">
                    </div>
                `);
            }
        });
}

// Event listeners

// Open/close
$(document).on("click", ".custom_dropdown-select", function (event) {
    $(".custom_dropdown-select").not($(this)).removeClass("open");
    if (!$(this).find("button").attr("disabled")) {
        if ($(event.target).hasClass("dd-searchbox")) {
            return;
        }
        $(this).toggleClass("open");
        if ($(this).hasClass("open")) {
            $(this).find(".active").focus();
            $(this).find(".dd-searchbox").focus();
        } else $(this).focus();
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
$(document).on("input", ".custom_dropdown-select .dd-searchbox", function () {
    var self = $(this);
    let select = self.closest(".custom_dropdown-select").next();
    var valThis = self.val();
    self.closest(".dropdown-menu")
        .find("li>.dropdown-item")
        .each(function () {
            let text = !select.hasAttr("multiple") ? $(this).text() : $(this).find("span").text();
            text.toLowerCase().indexOf(valThis.toLowerCase()) > -1 ? $(this).show() : $(this).hide();
        });
});

// Option click
$(document).on("click", ".custom_dropdown-select .dropdown-item", function () {
    setSelectCurrent({ context: "click", select: $(this).closest(".custom_dropdown-select")[0], selected: $(this)[0] });
});

$(document).on("click", ".custom_dropdown-select .current button", function (e) {
    e.stopPropagation();
    let button = $(this);
    button
        .closest(".custom_dropdown-select")
        .find("input[type='checkbox']")
        .each(function () {
            if (button.attr("data-id") == $(this).val()) {
                $(this).prop("checked", false);
                $(this).closest(".dropdown-item").removeClass("active select-active");
            }
        });
    button.parent().remove();
    setSelectCurrent({ select: select[0] });
});

// Keyboard events
$(document).on("keydown", ".custom_dropdown-select", function (event) {
    var focused_option = $($(this).find(".dropdown-item:focus")[0] || $(this).find(".dropdown-item.active")[0]);
    // Space or Enter
    //if (event.keyCode == 32 || event.keyCode == 13) {
    if (event.keyCode == 13) {
        if ($(this).hasClass("open")) focused_option.trigger("click");
        else $(this).trigger("click");
        return false;
        // Down
    } else if (event.keyCode == 40) {
        if (!$(this).hasClass("open")) $(this).trigger("click");
        else focused_option.parent().next().children().focus();
        return false;
        // Up
    } else if (event.keyCode == 38) {
        if (!$(this).hasClass("open")) $(this).trigger("click");
        else {
            var focused_option = $($(this).find(".dropdown-item:focus")[0] || $(this).find(".dropdown-item.active")[0]);
            focused_option.parent().prev().children().focus();
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
