const JSON_PATH = "/json/subreddits.json"

window.onload = () =>
{
    fetchSubreddits().then(data => fillSelect(data.subs))
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

async function fetchSubreddits()
{
    const response = await fetch(JSON_PATH)
    let data = await response.json()
    console.log(data)
    return data
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