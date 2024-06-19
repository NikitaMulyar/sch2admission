document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    submitButton.addEventListener('click', function(event) {
        myScript();
        const form = document.getElementById('myForm');
        submitButton.hidden = true;
        form.submit();
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
