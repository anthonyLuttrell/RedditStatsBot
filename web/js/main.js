const JSON_PATH = "/json/subreddits.json"

window.onload = () =>
{
    fetchSubreddits()
        .then(data => fillSelect(data.subs))
        .then(saveUserData()) // FIXME this isn't working right. saveUserData is being called before fillSelect has completed, so we are
};

function fillSelect(subs)
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

async function saveUserData()
{
    for (let sub in sessionStorage.getItem("subs"))
    {
        // Because these files are updated on the server every 6 hours, we need to avoid the browser cache each time a
        // user loads the web page. Appending "?<unique string>" to the end of the URL will avoid the cache.

        const path = "/json/" + sub + ".json?" + Date.now().toString();
        const response = await fetch(path);
        const data = await response.json();
        sessionStorage.setItem(sub, data.users.toString());
    }
}

async function fetchSubreddits()
{
    //
    const path = JSON_PATH.concat("?" + Date.now().toString());
    const response = await fetch(path);
    const data = await response.json();
    sessionStorage.setItem("subs", data.subs.toString());
    return data;
}

function displayUsers(users)
{
    const textArea = document.getElementById("output")
    for (let user in users)
    {
        for (let i = 0; i < users[user]["commentId"].length; i++)
        {
            textArea.value += users[user]["commentId"][i] + "   - -   " + users[user]["commentScore"][i] + "\r\n";
        }
    }
}