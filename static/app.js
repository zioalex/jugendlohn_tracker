document.addEventListener("DOMContentLoaded", function () {
    // === Button group selection (name buttons + category grid) ===
    document.addEventListener("click", function (e) {
        // Name buttons
        var nameBtn = e.target.closest(".btn-group [data-value]");
        if (nameBtn) {
            var group = nameBtn.closest(".btn-group");
            group.querySelectorAll("[data-value]").forEach(function (b) {
                b.classList.remove("active");
            });
            nameBtn.classList.add("active");
            var target = group.getAttribute("data-target");
            if (target) {
                document.getElementById(target).value = nameBtn.getAttribute("data-value");
            }
        }

        // Category buttons
        var catBtn = e.target.closest(".category-grid [data-value]");
        if (catBtn) {
            var grid = catBtn.closest(".category-grid");
            grid.querySelectorAll("[data-value]").forEach(function (b) {
                b.classList.remove("active");
            });
            catBtn.classList.add("active");
            var target2 = grid.getAttribute("data-target");
            if (target2) {
                document.getElementById(target2).value = catBtn.getAttribute("data-value");
            }
        }
    });

    // === Note toggle ===
    document.addEventListener("click", function (e) {
        if (e.target.closest(".note-toggle")) {
            var noteField = document.querySelector(".note-field");
            if (noteField) {
                noteField.classList.toggle("visible");
                if (noteField.classList.contains("visible")) {
                    noteField.querySelector("input, textarea").focus();
                }
            }
        }
    });

    // === Form validation ===
    var entryForm = document.getElementById("expense-form");
    if (entryForm) {
        entryForm.addEventListener("submit", function (e) {
            var name = document.getElementById("selected-name");
            var category = document.getElementById("selected-category");
            var amount = entryForm.querySelector("[name='amount']");

            var errors = [];
            if (name && !name.value) {
                errors.push(name.getAttribute("data-error") || "Please select a name.");
            }
            if (category && !category.value) {
                errors.push(category.getAttribute("data-error") || "Please select a category.");
            }
            if (amount && (!amount.value || parseFloat(amount.value) <= 0)) {
                errors.push(amount.getAttribute("data-error") || "Please enter a valid amount.");
            }

            if (errors.length > 0) {
                e.preventDefault();
                alert(errors.join("\n"));
            }
        });
    }

    // === Flash auto-dismiss ===
    var flashes = document.querySelectorAll(".flash-message");
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.classList.add("fade-out");
            setTimeout(function () {
                flash.remove();
            }, 300);
        }, 3000);
    });

    // === Delete confirmation ===
    document.addEventListener("click", function (e) {
        var deleteBtn = e.target.closest(".delete-btn");
        if (deleteBtn) {
            var msg = deleteBtn.getAttribute("data-confirm") || "Really delete?";
            if (!confirm(msg)) {
                e.preventDefault();
            }
        }
    });

    // === Setup: Add/Remove name rows ===
    document.addEventListener("click", function (e) {
        if (e.target.closest(".add-name-btn")) {
            var container = document.getElementById("names-container");
            if (!container) return;
            var rows = container.querySelectorAll(".name-row");
            var idx = rows.length;
            var row = document.createElement("div");
            row.className = "name-row";
            row.innerHTML =
                '<input type="text" name="name_' + idx + '" class="input-field" placeholder="Name">' +
                '<button type="button" class="btn btn-small btn-danger remove-name-btn">&times;</button>';
            container.appendChild(row);
        }

        if (e.target.closest(".remove-name-btn")) {
            var container2 = document.getElementById("names-container");
            if (!container2) return;
            var rows2 = container2.querySelectorAll(".name-row");
            if (rows2.length > 1) {
                e.target.closest(".name-row").remove();
            }
        }
    });

    // === Setup: Budget toggle ===
    document.addEventListener("change", function (e) {
        if (e.target.name === "budget_enabled") {
            var amountGroup = document.querySelector(".budget-amount-group");
            if (amountGroup) {
                amountGroup.style.display = e.target.value === "yes" ? "block" : "none";
            }
        }
    });

    // === Setup: Language selection buttons ===
    document.addEventListener("click", function (e) {
        var langBtn = e.target.closest(".lang-select-btn");
        if (langBtn) {
            document.querySelectorAll(".lang-select-btn").forEach(function (b) {
                b.classList.remove("active");
            });
            langBtn.classList.add("active");
            var langInput = document.getElementById("setup-language");
            if (langInput) {
                langInput.value = langBtn.getAttribute("data-value");
            }
        }
    });

    // === History: filter navigation ===
    document.addEventListener("change", function (e) {
        if (e.target.closest(".filter-bar select")) {
            var nameSelect = document.querySelector(".filter-bar [name='filter_name']");
            var monthSelect = document.querySelector(".filter-bar [name='filter_month']");
            var nameVal = nameSelect ? nameSelect.value : "";
            var monthVal = monthSelect ? monthSelect.value : "";
            var params = [];
            if (nameVal) params.push("name=" + encodeURIComponent(nameVal));
            if (monthVal) params.push("month=" + encodeURIComponent(monthVal));
            window.location = "/history" + (params.length ? "?" + params.join("&") : "");
        }
    });
});
