# PCworms Meeting Announcements
A simple Mustache template for [meet.pcworms.ir](https://meet.pcworms.ir)

## How It Works
For those who are curious and as a note for ourselves, this is how we create/update the webpage.

### What We Needed
- A simple webpage that provides information about the date, time, subject, and presenter
- A banner image for our social media
- A design that resembles our blog at [pcworms.ir](https://pcworms.ir)
- A straightforward way to update information, like updating a single JSON file
- A method to keep everyone on social media up to date
- Banner images that show up as the web preview on social media

### What We Came Up With
I [bsimjoo!](@b-simjoo) wrote a template using [Mustache](https://mustache.github.io/) syntax, then created a GitHub Action to generate the final webpage using the template and the JSON file. I also used Pageres to create images from the generated HTML file.
