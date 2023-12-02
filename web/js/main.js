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
    setSelectBoxWidth();
    fetchSubreddits()
        .then(data =>
        {
            fillSelectBox(data);
            saveUserData()
                .then(/* */);
        });
};

/**
 * After we fetch the list of subreddits, we use that response to populate the
 * HTML select element with the list of subreddits that the main app is looping
 * through. The user can select which subreddit they want to see results from.
 *
 * @param data
 */
function fillSelectBox(data)
{
    const selectBox = document.getElementById("subreddits-select");
    for (let i = 1; i <= data.subs.length; i++)
    {
        let option = document.createElement("option");
        option.value = i.toString();
        option.text = data.subs[i - 1];
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
        // make sure to use JSON.parse when parsing this data in session storage
        try
        {
            sessionStorage.setItem(sub, JSON.stringify(data));
            sessionStorage.setItem(sub + "-timestamp", JSON.stringify(data.timestamp));
        }
        catch (DOMException)
        {
            console.warn("SessionStorage is full! " + DOMException);
            break;
        }
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
    const footerText = document.getElementById("footer-timestamp");
    const subsArr = sessionStorage.getItem(SUBS_KEY).split(",");
    const users = JSON.parse(sessionStorage.getItem(subsArr[value - 1]));
    const totalsArray = getTotalsArray(users);

    // remove all rows when you select a different sub
    clearTable(table.rows.length);

    document.body.className = 'waiting';
    for (const user of totalsArray)
    {
        // TODO this can all be refactored into smaller nested functions
        const newRow = table.insertRow(table.rows.length);

        const newCell0 = newRow.insertCell(USERNAME_IDX);
        const newCell1 = newRow.insertCell(TOTAL_COMMENTS_IDX);
        const newCell2 = newRow.insertCell(TOTAL_SCORE_IDX);
        const newCell3 = newRow.insertCell(TOTAL_NEG_COMMENTS_IDX);

        newCell0.style.width = "40%";
        newCell1.style.width = "20%";
        newCell2.style.width = "20%";
        newCell3.style.width = "20%";

        const userName = document.createTextNode(truncateUsername(user));
        const totalComments = document.createTextNode(user[TOTAL_COMMENTS_IDX]);
        const totalScore = document.createTextNode(user[TOTAL_SCORE_IDX]);
        const totalNegatives = document.createTextNode(user[TOTAL_NEG_COMMENTS_IDX]);

        newCell0.appendChild(userName)
        newCell1.appendChild(totalComments);
        newCell2.appendChild(totalScore);
        newCell3.appendChild(totalNegatives);
    }

    // TODO convert this UTC string into the browser's local time
    //  see here: https://www.tutorialspoint.com/how-to-convert-utc-date-time-into-local-date-time-using-javascript
    footerText.innerText = "Last updated (UTC): " +
        JSON.parse(sessionStorage.getItem(subsArr[value - 1] + "-timestamp"))

    document.body.className = '';
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

function sortTableRowsByColumn( columnIndex, ascending )
{
    const table = document.getElementById("output-table");
    const rows = Array.from( table.querySelectorAll( ':scope > tbody > tr' ) );
    document.body.className = 'waiting';
    rows.sort( ( x, y ) => {

        const xValue = x.cells[columnIndex].textContent;
        const yValue = y.cells[columnIndex].textContent;

        const xNum = parseFloat( xValue );
        const yNum = parseFloat( yValue );

        return ascending ? ( xNum - yNum ) : ( yNum - xNum );
    } );

    const fragment = new DocumentFragment();
    for( let row of rows )
    {
        fragment.appendChild( row );
    }

    table.tBodies[0].appendChild( fragment );
    document.body.className = '';
}

/**
 * Sort table data based on a direction of asc or desc for a specific column
 * @param {number} n - column number calling this sort
 * @param {string} dir - direction of the sort (asc or desc)
 * @param {HTMLTableElement} targetElem - sort icon
 */
function sortTable(n, dir = "asc", targetElem) {
    targetElem.style.cursor = "progress";
    let sortArr = [];
    let table = targetElem.closest('table');
    table.querySelectorAll('tbody > tr > td:nth-Child(' + parseInt(n) + ')').forEach((x, y) => sortArr.push(
        {
            sortText: x.innerHTML.toLowerCase(),
            rowElement: x.closest('tr')
        }));
    var sorted = sortArr.sort(function (a, b) {
        if (dir == "asc") {
            if (a.sortText < b.sortText) {
                return -1;
            }
        } else if (dir == "desc") {
            if (a.sortText > b.sortText) {
                return -1;
            }
        }
        return 0;
    });
    sorted.forEach((x, y) => {
        x.rowElement.parentNode.insertBefore(x.rowElement, x.rowElement.parentNode.children[y]);
    });
    targetElem.style.cursor = null;
}

function setSelectBoxWidth()
{
    const selectBox = document.getElementById("subreddits-select");
    if (WINDOW_RATIO > 1.25)
    {
        selectBox.style.width = "25%";
        selectBox.style.maxWidth = "25%";
    }
}