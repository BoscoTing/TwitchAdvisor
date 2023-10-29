
let option = 'Average Message Count' // set default option 'Average Message Count'

currentDate = new Date();
startDate = new Date(currentDate.getFullYear(), 0, 1);
let days = Math.floor((currentDate - startDate) / (24 * 60 * 60 * 1000));
let week = Math.ceil(days / 7); // calculate week of year
let year = null;

function updateOverviewPlot(selectedWeek, selectedYear) {
    const loadingOverlay = document.getElementById("loadingOverlayOverview");
    loadingOverlay.style.display = "block";

    let xmlHttp = new XMLHttpRequest();
    if (selectedWeek && selectedYear) {
        xmlHttp.open( "GET", `/api/overview_data?week=${selectedWeek}&year=${selectedYear}`, true );
    }
    else {
        xmlHttp.open( "GET", `/api/overview_data`, true ); // use default week in flask
    };
    xmlHttp.onload = function () {
        loadingOverlay.style.display = "none";
        if (xmlHttp.status === 200) {
            let responseHtml = xmlHttp.responseText;
            let data = JSON.parse(responseHtml);

            // Extract unique channels
            const channels = [...new Set(data.map(entry => entry.channel))];
            const weekdays = ['Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.'];

            // Create data traces for each channel
            const traces = channels.map(channel => {
                const channelData = data.filter(entry => entry.channel === channel);
                const xValues = weekdays;
                const yValues = weekdays.map(weekday => {
                    const entry = channelData.find(dataEntry => dataEntry.weekDayName === weekday);

                    if (option == 'Average Message Count') {
                        return entry ? entry.avgMessageCount : 0;
                    }
                    else if (option == 'Highest Message Count') {
                        return entry ? entry.maxMessageCount : 0;
                    }
                    else if (option == 'Average Viewer Count') {
                        return entry ? entry.avgViewerCount : 0;
                    }
                    else if (option == 'Highest Viewer Count') {
                        return entry ? entry.maxViewerCount : 0;
                    }
                });

                return {
                    x: xValues,
                    y: yValues,
                    name: capitalizeNames([channel])[0],
                    mode: 'markers',
                    type: 'scatter',
                    marker: {"size": 12}
                };
            });

            // Create the layout
            const layout = {
                title: `Comparisons among Broadcasters at Week ${week}`,
                font: {
                    family: 'Verdana',
                    size: 15,
                },
                yaxis: {
                    title: option
                }, 
            };
            Plotly.react('overviewPlot', traces, layout);
        }
    };
    xmlHttp.send();
}

function capitalizeNames(names) {
    return names.map(name => {
      // Capitalize the first letter of each word and handle "lol" pattern
      return name.replace(/\b\w/g, firstLetter => firstLetter.toUpperCase()).replace(/_lol\b/gi, ' LOL');
    });
  }

// add event listener on week selector of html.
function handleWeekSelection() {

    const weekInput = document.getElementById("week");
    const selectedWeek = weekInput.value;
    const regex = /(\d+)-W(\d+)/;
    const match = selectedWeek.match(regex);
    if (match) {
        year = match[1];
        week = match[2];
        updateOverviewPlot(week, year);
    } else {
        console.log('No match found.');
    };
}

const overviewMetricsSelect = document.getElementById("overviewMetricsSelect")

overviewMetricsSelect.addEventListener ("change", function () {
    option = overviewMetricsSelect.value;
    updateOverviewPlot(week, year);
})

updateOverviewPlot();