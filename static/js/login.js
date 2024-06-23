document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    const form = document.getElementById('myForm');
    const collapseContent = document.getElementById("collapseExample");
    const bsCollapse = new bootstrap.Collapse(collapseContent, {toggle: false});

    form.addEventListener('submit', function(event) {
        bsCollapse.show();
        submitButton.hidden = true;
        setTimeout(function() {
            bsCollapse.hide();
            submitButton.hidden = false;
        }, 3000);
        form.submit();
    });
});
