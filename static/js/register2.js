document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    const selectField = document.getElementById("class_number");
    const showDiv = document.getElementById("myProfile");
    const form = document.getElementById('myForm');
    showDiv.hidden = true;

    submitButton.addEventListener('click', function(event) {
        myScript();
        const submitButton = document.getElementById('myBtn');
        const form = document.getElementById('myForm');
        submitButton.hidden = true;
        form.submit();
    });

    form.addEventListener('change', function(event) {
        const showDiv = document.getElementById("myProfile");
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
    }, 10000);
}
