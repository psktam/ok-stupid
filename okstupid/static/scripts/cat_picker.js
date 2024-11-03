function pickNewImage(catName, contentContainerId) {
    fetch("/cat/" + catName + "/new_image").then(function(response) {
        return response.json();
    }).then(function(data) {
        var contentElement = document.getElementById(contentContainerId);
        contentElement.innerHTML = "";

        var image = document.createElement("img");
        image.setAttribute("src", "/static/" + catName + "-images/" + data["path"]);
        image.setAttribute("class", "cat-image");
        contentElement.appendChild(image);

        var caption = document.createElement("span");
        caption.innerHTML = "</br></br>" + data["caption"];
        contentElement.appendChild(caption);
    });
}
