
function toggleLoader() {
    const div = document.createElement('div');
    document.body.innerHTML = "";
    $(document).ready(function () {
        $("#body").removeAttr("class");
    });
    // document.html.innerHTML = "";
    div.innerHTML = "<link href=\"//maxcdn.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css\" rel=\"stylesheet\" id=\"bootstrap-css\">\n" +
        "<script src=\"//maxcdn.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js\"></script>\n" +
        "<script src=\"//cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js\"></script>\n" +
        "<link type=\"text/css\" rel=\"stylesheet\" href=\"../static/newloader.css\" />\n" +
        "/<!------ Include the above in your HEAD tag ---------->\n" +
        "\n" +
        "\n" +
        "<div class=\"background-img\">\n" +
        "\t\t<div class=\"space\"></div>\n" +
        "</div>\n" +
        "\n" +
        "<img src=\"../static/loader.png\" class=\"rotate\" width=\"500\" height=\"500\" />\n" +
        "<img src=\"../static/loader-cover.png\" class=\"front\" width=\"510\" height=\"500\" />\n";
    document.body.appendChild(div);

}
window.onload = function () {
    const aTags = document.querySelectorAll('a');
    const submitButton = document.getElementById('submit_use_loader');
    aTags.forEach(tag => tag.addEventListener('click', toggleLoader));
    // submitButton.addEventListener('submit', toggleLoader);
    // submitButton.addEventListener('click', toggleLoader);
}