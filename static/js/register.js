document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    const form = document.getElementById('myForm');
    const collapseContent = document.getElementById("collapseExample");
    const bsCollapse = new bootstrap.Collapse(collapseContent, {toggle: false});

    form.addEventListener('submit', function(event) {
        alert(10);
        bsCollapse.show();
        submitButton.hidden = true;
        setTimeout(function() {
            bsCollapse.hide();
            submitButton.hidden = false;
        }, 10000);
        form.submit();
    });

    const selectField = document.getElementById("class_number");
    const showDiv = document.getElementById("myProfile");
    showDiv.hidden = !(selectField.value === "10" || selectField.value === "11");
    selectField.addEventListener('change', function(event) {
        showDiv.hidden = !(selectField.value === "10" || selectField.value === "11");
    });
});
