function updateLiveChannels() {
    var xmlHttp = new XMLHttpRequest();
    var host = window.location.host; 
    xmlHttp.open( "GET", `/api/update_channels`, false ); // get top live channels through twitchAPI
    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            var responseHtml = xmlHttp.responseText;
            var responseJson = JSON.parse(responseHtml);

            const category = responseJson.data;
            let justChatting = category.just_chatting;
            let leagueOfLegends = category.league_of_legends; 
            let music = category.music;

            const topLiveChannels = document.querySelector("#topLiveChannels"); // title of "Top Live Channels"

            const ulElement = document.createElement("div"); // create a list under this title
            ulElement.setAttribute("id", "updateLiveChannels");
            ulElement.setAttribute("class", "channels");
            ulElement.setAttribute("class", "columns");

            // console.log("topLiveChannels.childElementCount:", topLiveChannels.childElementCount)
            if (topLiveChannels.childElementCount > 0) { // clear the channels under "Top Live Channels" before updating results.
                let oldUlElement = document.getElementById("updateLiveChannels");
                document.getElementById("topLiveChannels").removeChild(oldUlElement); 
                console.log("clear previous topLiveChannels")
            };

            for (var i = 0; i < leagueOfLegends.length; i++) { // update live channel list.
                
                const liElement = document.createElement("p");
                liElement.textContent = leagueOfLegends[i];
                liElement.setAttribute("class", "liveChannels")
                ulElement.appendChild(liElement);
            };
            topLiveChannels.appendChild(ulElement);
        }
    }
    xmlHttp.send();
    console.log("Update live channels")
};

updateLiveChannels();
var updateInterval = setInterval(updateLiveChannels, 60000); // update in every 1 minutes.
