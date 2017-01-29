# git2dot
Visualize a git repository using the graphviz dot tool.

It is useful for understanding how git works in detail.  You can use
it to analyze repositories before and after operations like merge and
rebase to really get a feeling for what happens. It can also be used
for looking at subsets of history on live repositories.

Here is an example that shows the PNG file generated by test04 in the
test directory.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://cloud.githubusercontent.com/assets/2991242/22406472/8a5cb046-e608-11e6-9365-bd40c571d304.png" alt="test04 example">

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
the generated data for re-use, customizing dot directly and
generating graphical output like PNG, SVG or even HTML files.

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

You can choose to keep the git output to re-use multiple times with
different display options or to share by specifying the `-k` (`--keep`)
option.

Use the `-h` option to get detailed information about the available options.

## Example
The following example shows how to use git2dot by creating a git repository
from scratch and then running the tool to create images.

First we create a repository with a bunch of commits and branches.
```bash
git init

echo 'A' >README
git add README
git commit -m 'master - first'
sleep 1

echo 'B' >>README
git add README
git commit -m 'master - second' -m 'Change-Id: I001'
sleep 1

# tag the basis for all of the branches
git tag -a 'v1.0' -m 'Initial version.'
git tag -a 'v1.0a' -m 'Another version.'

git checkout -b branchX1
git checkout master
git checkout -b branchX2

git checkout master
git checkout -b branchA
echo 'C' >> README
git add README
git commit -m 'branchA - first'
sleep 1

echo 'B' >> README
git add README
git commit -m 'branchA - second' -m 'Change-Id: I001'
sleep 1

git checkout master
git checkout -b branchB
echo 'E' >> README
git add README
git commit -m 'branchB - first'
sleep 1

echo 'F' >> README
git add README
git commit -m 'branchB - second'
sleep 1

echo 'B' >> README
git add README
git commit -m 'branchB - third' -m 'Change-Id: I001'
sleep 1

echo 'H' >> README
git add README
git commit -m 'branchB - fourth' -m 'Change-Id: I002'
sleep 1

echo 'I' >> README
git add README
git commit -m 'branchB - fifth'
sleep 1

echo 'J' >> README
git add README
git commit -m 'branchB - sixth'
sleep 1

echo 'K' >> README
git add README
git commit -m 'branchB - seventh'
sleep 1

git checkout master
echo 'L' >> README
git add README
git commit -m 'master - third'
```

You can verify using something like `git log`.
```bash
$ git log --graph --oneline --decorate --all
* 7fd1f5d (HEAD -> master) master - third
| * 98b994f (branchB) branchB - seventh
| * 00dda04 branchB - sixth
| * 01895af branchB - fifth
| * 84fa67d branchB - fourth
| * f8e33ec branchB - third
| * 7b66d32 branchB - second
| * 3385e18 branchB - first
|/  
| * cced7be (branchA) branchA - second
| * 843d5ce branchA - first
|/  
* 46407c4 (tag: v1.0a, tag: v1.0, branchX2, branchX1) master - second
* 84ca47b master - first
```

Now run the git2dot tool to generate PNG, HTML and SVG files.
```bash
$ git2dot.py --png --svg --html example.html example.dot
$ ls -1 example.*
example.dot
example.dot.png
example.dot.svg
example.html
```

You can now view the PNG and SVG files using local tools.
```bash
$ open -a Preview example.dot.png  # on Mac
$ display example.dot.png          # on Linux
```

To view the generated SVG file with pan and zoom you must download
the svg-pan-zoom.min.js file from https://github.com/ariutta/svg-pan-zoom
and copy into the current directory.

```bash
$ cp ~/work/svg-pan-zoom-3.4.1/dist/svg-pan-zoom.min.js .
$ ls -1 example* svg*
example.dot
example.dot.png
example.dot.svg
example.html
svg-pan-zoom.min.js
```

Now you need to start a server.

```bash
$  python -m SimpleHTTPServer 8090
```

After that you can browse to http://localhost:8090/example.html and you will see this.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://cloud.githubusercontent.com/assets/2991242/22406665/d5f7ca60-e60b-11e6-957f-ff6a9536b615.png" width="1100" alt="example">
