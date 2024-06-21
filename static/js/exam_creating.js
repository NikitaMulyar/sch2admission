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
    showDiv.hidden = true;
    selectField.addEventListener('change', function(event) {
        showDiv.hidden = !(selectField.value === "10" || selectField.value === "11");
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
