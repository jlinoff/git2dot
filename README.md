# git2dot
Visualize a git repository using the graphviz dot tool.

It is useful for understanding how git works in detail.  You can use
it to analyze repositories before and after operations like merge and
rebase to really get a feeling for what happens. It can also be used
for looking at subsets of history on live repositories.

It works by running over the .git repository in the current directory
and generating a commit relationship DAG that has both parent and
child relationships.

The generated graph shows commits, tags and branches as nodes.
Commits are further broken down into simple commits and merged commits
where merged commits are commits with 2 or more children. There is an
additional option that allows you to squash long chains of simple
commits with no branch or tag data.

It has a number of different options for customizing the nodes,
using your own custom git command to generate the data, keeping
the generated data for re-use and generating graphical output like
PNG, SVG or even HTML files.

Here is an example run:
```bash
   $ cd SANDBOX
   $ git2dot.py --png git.dot
   $ open -a Preview git.dot.png  # on Mac OS X
   $ display git.dot.png          # linux
```
If you want to create a simple HTML page that allows panning and
zooming of the generated SVG then use the --html option like
this.
```bash
   $ cd SANDBOX
   $ git2dot.py --svg --html ~/web/index.html ~/web/git.dot
   $ $ ls ~/web
   git.dot          git.dot.svg      git.html         svg-pan-zoom.js
   $ cd ~/web
   $ python -m SimpleHTTPServer 8090  # start server
   $ # Browse to http://localhost:8090/git.dot.svg
   ```

It assumes that existence of svg-pan-zoom.js from the
https://github.com/ariutta/svg-pan-zoom package.

The output is pretty customizable. For example, to add the subject and
commit date to the commit node names use `-l '%s|%cr'`. The items come
from the git format placeholders or variables that you define using
`-D`. The | separator is used to define the end of a line. The maximum
width of each line can be specified by `-w`. Variables are defined by `-D`
and come from text in the commit message. See `-D` for more details.

You can customize the attributes of the different types of nodes and
edges in the graph using the -?node and -?edge attributes. The table
below briefly describes the different node types:

| Node Type | Brief Description |
| --------- | ----------------- |
|  bedge    | Edge connecting to a bnode. |
|  bnode    | Branch node associated with a commit. |
|  cnode    | Commit node (simple commit node). |
|  mnode    | Merge node. A commit node with multiple children. |
|  snode    | Squashed node. End point of a sequence of squashed nodes. |
|  tedge    | Edge connecting to a tnode. |
|  tnode    | Tag node associated with a commit. |

If you have long chains of single commits use the `--squash` option to
squash out the middle ones. That is generally helpful for filtering
out extraneous commit details for moderately sized repos.

If you want to limit the analysis to commits between certain dates,
use the `--since` and `--until` options.

If you want to limit the analysis to commits in a certain range use
the `--range` option.

You can chose to keep the git output to re-use multiple times with
different display options or to share by specifying the `-k` (`--keep`)
option.
