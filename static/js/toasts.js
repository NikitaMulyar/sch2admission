const toastContent = document.querySelectorAll(".toast")
for (let i = 0; i < toastContent.length; i++) {
    const toast = new bootstrap.Toast(toastContent[i]);
    toast.show();
}
