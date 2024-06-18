document.addEventListener('DOMContentLoaded', function() {
    var submitButton = document.getElementById('myBtn');
    submitButton.addEventListener('click', function(event) {
        myScript();
        var form = document.getElementById('myForm');
        form.submit();
    });
});

function myScript() {
    const collapseContent = document.getElementById("collapseExample");
    const bsCollapse = new bootstrap.Collapse(collapseContent);
    bsCollapse.show();
    setTimeout(function() {
        bsCollapse.hide();
    }, 5000);
}
