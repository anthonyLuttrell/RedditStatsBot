const JSON_PATH = "/json/";
const JSON_QUERY = ".json?" + Date.now().toString();
const SUBS_STRING = "subreddits";
const SUBS_KEY = "subs";
const USERNAME_IDX = 0;
const TOTAL_COMMENTS_IDX = 1;
const TOTAL_SCORE_IDX = 2;
const TOTAL_NEG_COMMENTS_IDX = 3;
const WINDOW_RATIO = window.innerWidth / window.innerHeight;

window.onload = () =>
{
    fetchSubreddits()
        .then(data =>
        {
            fillSelectBox(data.subs);
            saveUserData()
                .then(/* FIXME add timestamp to JSON, add to footer */);
        });
};

/**
 * After we fetch the list of subreddits, we use that response to populate the
 * HTML select element with the list of subreddits that the main app is looping
 * through. The user can select which subreddit they want to see results from.
 *
 * @param subs
 */
function fillSelectBox(subs)
{
    const selectBox = document.getElementById("subreddits-select");
    for (let i = 1; i <= subs.length; i++)
    {
        let option = document.createElement("option");
        option.value = i.toString();
        option.text = subs[i - 1];
        selectBox.add(option);
    }
}

/**
 * Saves the user data for each JSON file to session storage. We loop through a
 * comma-separated list in session storage to get each sub's name, which
 * corresponds to a JSON file where the user data is saved. Because these files
 * are updated on the server every 6 hours, we need to avoid the browser cache
 * each time a user loads the web page. Appending "?<unique string>" to the end
 * of the URL will avoid the cache.
 *
 * @returns {Promise<void>}
 */
async function saveUserData()
{
    const subsArr = sessionStorage.getItem(SUBS_KEY).split(",");
    for (const sub of subsArr)
    {
        const path = JSON_PATH + sub + JSON_QUERY;
        const response = await fetch(path);
        const data = await response.json();
        sessionStorage.setItem(sub, JSON.stringify(data)); // make sure to use JSON.parse when parsing this data in session storage
    }
}

/**
 * We fetch a list of subreddits from the "subreddits.json" file saved to the
 * webserver, and we save it to one long comma-separated string in session
 * storage.
 *
 * @returns {Promise<any>}
 */
async function fetchSubreddits()
{
    const path = JSON_PATH + SUBS_STRING + JSON_QUERY;
    const response = await fetch(path);
    const data = await response.json();
    sessionStorage.setItem(SUBS_KEY, data.subs.toString());
    return data;
}

/**
 * Displays a summary of each user's comment history.
 *
 * @param value
 */
function displayAllUsers(value)
{
    if (value === "0")
    {   // value is 0 when user selects the default select box option, so don't do anything in that case
        return;
    }

    const table = document.getElementById("output-table").getElementsByTagName("tbody")[0];
    const subsArr = sessionStorage.getItem(SUBS_KEY).split(",");
    const users = JSON.parse(sessionStorage.getItem(subsArr[value - 1]));
    const totalsArray = getTotalsArray(users);

    // remove all rows when you select a different sub
    clearTable(table.rows.length);

    for (const user of totalsArray)
    {
        // TODO this can all be refactored into smaller nested functions
        const truncatedUsername = truncateUsername(user);

        const newRow = table.insertRow(table.rows.length);

        const newCell0 = newRow.insertCell(USERNAME_IDX);
        const newCell1 = newRow.insertCell(TOTAL_COMMENTS_IDX);
        const newCell2 = newRow.insertCell(TOTAL_SCORE_IDX);
        const newCell3 = newRow.insertCell(TOTAL_NEG_COMMENTS_IDX);

        const userName = document.createTextNode(truncatedUsername);
        const totalComments = document.createTextNode(user[TOTAL_COMMENTS_IDX]);
        const totalScore = document.createTextNode(user[TOTAL_SCORE_IDX]);
        const totalNegatives = document.createTextNode(user[TOTAL_NEG_COMMENTS_IDX]);

        newCell0.appendChild(userName)
        newCell1.appendChild(totalComments);
        newCell2.appendChild(totalScore);
        newCell3.appendChild(totalNegatives);

        newCell0.style.width = "40%";
        newCell1.style.width = "20%";
        newCell2.style.width = "20%";
        newCell3.style.width = "20%";
    }
}

function truncateUsername(user)
{
    let userNameString = user[0]

    if (WINDOW_RATIO < 0.70 && user[USERNAME_IDX].length > 11)
    {   // truncate the username because we are short on horizontal space
        userNameString = user[0].slice(0, 12);
        userNameString += "...";
    }
    else if (user[USERNAME_IDX].length > 25)
    {   // Reddit username character limit is 36
        userNameString = user[0].slice(0, 26);
        userNameString += "...";
    }

    return userNameString;
}

/**
 * Builds the totals array. Loop through the usersObj, adding up the total number of comments, the total score, and the total number of
 *     comments with a negative score.
 *
 *     For example: [["bob",31,278,0],["jane",12,773,2]]
 *
 * @param usersObj - A key-value pair object that contains the user ID, and each comment ID and comment score.
 * @returns {*[]} - For example: [["bob",31,278,0],["jane",12,773,2]]
 */
function getTotalsArray(usersObj)
{
    const totalsArray = [];

    if (typeof usersObj !== "object")
    {
        console.warn("Incompatible datatype")
        return totalsArray;
    }

    for (const user in usersObj.users)
    {
        let totalUserComments = 0;
        let totalUserScore = 0;
        let totalNegativeComments = 0;

        for (const score of usersObj.users[user].commentScore)
        {
            totalUserComments++;
            totalUserScore += score;
            if (score < 0)
            {
                totalNegativeComments++;
            }
        }

        totalsArray.push([user, totalUserComments, totalUserScore, totalNegativeComments]);
    }

    return totalsArray;
}

function filterInput()
{
    const input = document.getElementById("search-box");
    const filter = input.value.toUpperCase();
    const table = document.getElementById("output-table");
    const tr = table.getElementsByTagName("tr");

    for (let i = 0; i < tr.length; i++)
    {
        const td = tr[i].getElementsByTagName("td")[0];
        if (td)
        {
            let txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1)
            {
                tr[i].style.display = "";
            }
            else
            {
                tr[i].style.display = "none";
            }
        }
    }
}

function clearTable(tableLength)
{
    const table = document.getElementById("output-table").getElementsByTagName("tbody")[0]
    for (let i = 0; i < tableLength; i++)
    {
        table.deleteRow(-1);
    }
}

function sortTable(n)
{
    // FIXME this is super ugly and slow code stolen from here: https://www.w3schools.com/howto/howto_js_sort_table.asp
    //  this should be cleaned up and optimized. It is only sorting by name, not by integer.
    //  see here: https://stackoverflow.com/questions/11304490/quick-html-table-sorting
    //  and here: https://stackoverflow.com/questions/59282842/how-to-make-sorting-html-tables-faster
    var table,
        rows,
        switching,
        i,
        x,
        y,
        shouldSwitch,
        dir,
        switchcount = 0;
    table = document.getElementById("output-table");
    switching = true;
    // Set the sorting direction to ascending:
    dir = "asc";
    /* Make a loop that will continue until
    no switching has been done: */
    while (switching)
    {
        // Start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        /* Loop through all table rows (except the
        first, which contains table headers): */
        for (i = 1; i < (rows.length - 1); i++)
        {
            // Start by saying there should be no switching:
            shouldSwitch = false;
            /* Get the two elements you want to compare,
            one from current row and one from the next: */
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            /* Check if the two rows should switch place,
            based on the direction, asc or desc: */
            if (dir == "asc")
            {
                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase())
                {
                    // If so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                }
            }
            else if (dir == "desc")
            {
                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase())
                {
                    // If so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch)
        {
            /* If a switch has been marked, make the switch
            and mark that a switch has been done: */
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            // Each time a switch is done, increase this count by 1:
            switchcount++;
        }
        else
        {
            /* If no switching has been done AND the direction is "asc",
            set the direction to "desc" and run the while loop again. */
            if (switchcount == 0 && dir == "asc")
            {
                dir = "desc";
                switching = true;
            }
        }
    }
}