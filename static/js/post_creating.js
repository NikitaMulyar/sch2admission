document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    const backButton = document.getElementById('buttons-style');
    const form = document.getElementById('myForm');
    const collapseContent = document.getElementById("collapseExample");
    const bsCollapse = new bootstrap.Collapse(collapseContent, {toggle: false});

    form.addEventListener('submit', function(event) {
        bsCollapse.show();
        submitButton.hidden = true;
        backButton.hidden = true;
        setTimeout(function() {
            bsCollapse.hide();
            submitButton.hidden = false;
            backButton.hidden = false;
        }, 3000);
        form.submit();
    });

    const selectField = document.getElementById("all-classes");
    const fields = document.getElementsByClassName("class-field");

    for (let i = 0; i < fields.length; i++) {
        fields[i].addEventListener('click', function(event) {
            if (!fields[i].checked) {
                selectField.checked = false;
            }
            let all_ = true;
            for (let i = 0; i < fields.length; i++) {
                if (!fields[i].checked) {
                    all_ = false;
                    break;
                }
            }
            if (all_) {
                selectField.checked = true;
            }
        });
    }

    selectField.addEventListener('click', function(event) {
        for (let i = 0; i < fields.length; i++) {
            fields[i].checked = selectField.checked;
        }
    });
});
