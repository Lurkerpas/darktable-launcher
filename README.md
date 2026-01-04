# darktable-launcher
Simple launcher for darktable which allows to select the current DB.
For more about darktable, an open source photography workflow application, please visit https://www.darktable.org/
Please note that the project and the author are not affilated in any way with the darktable project.

# rationale
Darktable uses a single database file to store catalogue metadata. The recommended way to manage various catalogues is to use tags, filters, etc. Rationale for this decision is explained in many places and I am not willing to dispute it. However, it does not fit my workflow, in which I have probably over a hundred catalogues, with hundreds or thousands of photos each, sorted into subcollections (picking phases, backstage, per-person, etc) via tags, stars and colors. These catalogues, in time, move between my drives, from local to network/DVD/BD. Therefore, I prefer the Lightroom's photo management approach. However, due to various circumstances, I am in the process of minimizing my dependency on Microsoft and Adobe products, and that includes ensuring both access to my previous catalogues, created in Lightroom, and efficient management of new ones, preferably created using open source software. This piece of software aims to address the second issue. It has been created for personal use, with no foreseen maintenance, however, I will be happy if someone finds it useful.

Various sources recommend launching darktable from terminal with "--library" option (documented here https://darktable-org.github.io/dtdocs/en/special-topics/program-invocation/darktable/) to select the current catalogue/workspace. This application wraps this functionality in a GUI, which additionally stores the list of recent catalogues.

The application is meant to be as simple as possible, with as few dependencies as possible.

# usage
Install via:
`make install`

Install app shortcut (tested on Ubuntu):
`make desktop-launcher`

Launch:
Type `darktable-launcher` in terminal or app launcher (if app shortcut was previously created).

Darktable itself needs to be installed separately.
