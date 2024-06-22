document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('myBtn');
    const form = document.getElementById('myForm');
    submitButton.addEventListener('click', function(event) {
        myScript();
        submitButton.hidden = true;
        form.submit();
    });

    const checkBox1 = document.getElementById("checkBox1");
    const checkBox2 = document.getElementById("checkBox2");
    const checkBox1Text = document.getElementById("checkBox1-text");
    const checkBox2Text = document.getElementById("checkBox2-text");
    checkBox1Text.style.fontWeight = 'bold';
    checkBox2Text.style.fontWeight = 'bold';
    setColorText1(1);
    setColorText2(1);
    checkBox1.addEventListener('change', setColorText1);
    checkBox2.addEventListener('change', setColorText2);
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

function setColorText1(event) {
    const checkBox1 = document.getElementById("checkBox1");
    const checkBox1Text = document.getElementById("checkBox1-text");
    if (checkBox1.checked) {
        checkBox1Text.textContent = "ОТКРЫТА";
        checkBox1Text.style["color"] = "#198754";
    } else {
        checkBox1Text.textContent = "ЗАКРЫТА";
        checkBox1Text.style["color"] = "#dc3545";
    }
}

function setColorText2(event) {
    const checkBox2 = document.getElementById("checkBox2");
    const checkBox2Text = document.getElementById("checkBox2-text");
    if (checkBox2.checked) {
        checkBox2Text.textContent = "ОТКРЫТА";
        checkBox2Text.style["color"] = "#198754";
    } else {
        checkBox2Text.textContent = "ЗАКРЫТА";
        checkBox2Text.style["color"] = "#dc3545";
    }
}