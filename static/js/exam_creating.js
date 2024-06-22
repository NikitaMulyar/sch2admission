document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    const form = document.getElementById('myForm');
    submitButton.addEventListener('click', function(event) {
        myScript();
        submitButton.hidden = true;
        form.submit();
    });

    const selectField = document.getElementById("class_number");
    const showDiv = document.getElementById("myProfile");
    showDiv.hidden = !(selectField.value === "10" || selectField.value === "11");
    selectField.addEventListener('change', function(event) {
        showDiv.hidden = !(selectField.value === "10" || selectField.value === "11");
    });

    const selectField_title = document.getElementById("title");
    const showDiv2 = document.getElementById("other-title");
    showDiv2.hidden = !(selectField_title.value === "Другое");
    selectField_title.addEventListener('change', function(event) {
        showDiv2.hidden = !(selectField_title.value === "Другое");
    });
});

function myScript() {
    const collapseContent = document.getElementById("collapseExample");
    const bsCollapse = new bootstrap.Collapse(collapseContent);
    bsCollapse.show();
    const submitButton = document.getElementById('myBtn');
    setTimeout(function() {
        bsCollapse.hide();
        submitButton.hidden = false;
    }, 3000);
}
