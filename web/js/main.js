const JSON_PATH = "/json/"
const JSON_QUERY = ".json?" + Date.now().toString()
const SUBS_STRING = "subreddits"
const SUBS_KEY = "subs"

window.onload = () =>
{
    fetchSubreddits()
        .then(data =>
        {
            fillSelectBox(data.subs);
            saveUserData()
                .then(/*  */);
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
 * Username                             | Number of Comments | Total Score | Number of Negative Comments
 * xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | xxxx               | xxxxx       | xxx
 *
 * TODO need to figure out a better way to display this data. Maximum Reddit username characters is 36
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
    clearTable(table);

    for (const user of totalsArray)
    {
        const newRow = table.insertRow(table.rows.length);
        const newCell0 = newRow.insertCell(0);
        const newCell1 = newRow.insertCell(1);
        const newCell2 = newRow.insertCell(2);
        const newCell3 = newRow.insertCell(3);
        const userName = document.createTextNode(user[0]);
        const totalComments = document.createTextNode(user[1]);
        const totalScore = document.createTextNode(user[2]);
        const totalNegatives = document.createTextNode(user[3]);
        // FIXME truncate username text if it's over a certain character limit
        newCell0.appendChild(userName)
        newCell1.appendChild(totalComments);
        newCell2.appendChild(totalScore);
        newCell3.appendChild(totalNegatives);
        newCell0.style.width = "33%";
        newCell1.style.width = "22.3%";
        newCell2.style.width = "22.3%";
        newCell3.style.width = "22.3%";
    }
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

function clearTable(table)
{
    for (const row of table)
    {   // FIXME this isn't working, table is not iterable
        row.remove();
    }
}