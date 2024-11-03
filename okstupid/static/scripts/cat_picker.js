function pickNewImage(catName, contentContainerId) {
    fetch("/cat/" + catName + "/new_image").then(function(response) {
        return response.json();
    }).then(function(data) {
        var contentElement = document.getElementById(contentContainerId);
        contentElement.innerHTML = "";

        var image = document.createElement("img");
        image.setAttribute("src", "/static/" + catName + "-images/" + data["path"]);
        image.setAttribute("class", "cat-image");
        var aspectRatio = data["size"][0] / data["size"][1];
        var maxDimension = 95;
        // } else {
        //     image.style.height = maxDimension.toString() + "em";
        //     image.style.width = (maxDimension * aspectRatio).toString() + "em";
        // }
        contentElement.appendChild(image);
    });
}
