function onYouTubeIframeAPIReady() {
    window.addEventListener("load", function() {
        var ctrlq = document.getElementById("youtube-audio");

        var icon = document.createElement("img");
        icon.setAttribute("id", "youtube-icon");
        icon.style.cssText = "cursor:pointer;cursor:hand";
        ctrlq.appendChild(icon);

        var div = document.createElement("div");
        div.setAttribute("id", "youtube-player");
        ctrlq.appendChild(div);

        var playState = false;

        var toggleButton = function (play, active) {
            var prefix = play ? "stop" : "play";
            var suffix = active ? "-active" : "";
            var img = prefix + "-button" + suffix + ".png";
            icon.setAttribute("src", "/static/" + img);
        }

        ctrlq.onclick = function() {
            if (player.getPlayerState() === YT.PlayerState.PLAYING
                || player.getPlayerState() === YT.PlayerState.BUFFERING) {

                player.pauseVideo();
                toggleButton(false, true);
                playState = false;
            } else {
                player.playVideo();
                toggleButton(true, true);
                playState = true;
            }
        };

        ctrlq.onmouseover = function() {
            toggleButton(playState, true);
        }
        ctrlq.onmouseout = function() {
            toggleButton(playState, false);
        }

        var player = new YT.Player('youtube-player', {
            height: '0',
            weidth: '0',
            videoId: ctrlq.dataset.video,
            playerVars: {
                autoplay: ctrlq.dataset.autoplay,
                loop: ctrlq.dataset.loop,
            },
            events: {
                'onReady': function(e) {
                    player.setPlaybackQuality("small");
                    toggleButton(player.getPlayerState() !== YT.PlayerState.CUED);
                },
                'onStateChange': function(e) {
                    if (e.data === YT.PlayerState.ENDED) {
                        toggleButton(false);
                    }
                }
            }
        });
    });
}
