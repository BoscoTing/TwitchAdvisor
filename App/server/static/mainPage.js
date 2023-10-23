function updateLiveChannels() {
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", `/api/update_channels`, false ); // get top live channels through twitchAPI
    xmlHttp.onload = function () {
        if (xmlHttp.status === 200) {
            let responseHtml = xmlHttp.responseText;
            let responseJson = JSON.parse(responseHtml);

            const category = responseJson.data;
            let leagueOfLegends = category.league_of_legends; 

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

            for (let i = 0; i < leagueOfLegends.length; i++) { // update live channel list.
                
                const liElement = document.createElement("p");
                liElement.textContent = leagueOfLegends[i];
                liElement.setAttribute("class", "liveChannels")
                ulElement.appendChild(liElement);
            };
            topLiveChannels.appendChild(ulElement);
        }
    }
    xmlHttp.send();
};