function dismissFlashMessage() {

    fetch('/dismiss_flash')
        .then(response => {
        // remove flash message from the HTML
            var flash = document.getElementById("flash-message");
            flash.parentNode.removeChild(flash);
        })
        .catch(error => {
            console.error('Error dismissing flash message:', error);
        });
}