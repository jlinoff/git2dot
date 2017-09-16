#!/usr/bin/env python
r'''
Tool to visualize a git repository using the graphviz dot tool.

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

   $ cd SANDBOX
   $ git2dot.py --png git.dot
   $ open -a Preview git.dot.png  # on Mac OS X
   $ display git.dot.png          # linux

If you want to create a simple HTML page that allows panning and
zooming of the generated SVG then use the --html option like
this.

   $ cd SANDBOX
   $ git2dot.py --svg --html ~/web/index.html ~/web/git.dot
   $ $ ls ~/web
   git.dot          git.dot.svg      git.html         svg-pan-zoom.min.js
   $ cd ~/web
   $ python -m SimpleHTTPServer 8090  # start server
   $ # Browse to http://localhost:8090/git.dot.svg

It assumes that existence of svg-pan-zoom.min.js from the
https://github.com/ariutta/svg-pan-zoom package.

The output is pretty customizable. For example, to add the subject and
commit date to the commit node names use -l '%s|%cr'. The items come
from the git format placeholders or variables that you define using
-D. The | separator is used to define the end of a line. The maximum
width of each line can be specified by -w. Variables are defined by -D
and come from text in the commit message. See -D for more details.

You can customize the attributes of the different types of nodes and
edges in the graph using the -?node and -?edge attributes. The table
below briefly describes the different node types:

   bedge     Edge connecting to a bnode.
   bnode     Branch node associated with a commit.
   cnode     Commit node (simple commit node).
   mnode     Merge node. A commit node with multiple children.
   snode     Squashed node. End point of a sequence of squashed nodes.
   tedge     Edge connecting to a tnode.
   tnode     Tag node associated with a commit.

If you have long chains of single commits use the --squash option to
squash out the middle ones. That is generally helpful for filtering
out extraneous commit details for moderately sized repos.

If you find that dot is placing your bnode and tnode nodes in odd
places, use the --crunch option to collapse the bnode nodes into
a single node and the tnodes into a single node for each commit.

If you want to limit the analysis to commits between certain dates,
use the --since and --until options.

If you want to limit the analysis to commits in a certain range use
the --range option.

If you want to limit the analysis to a small set of branches or tags
you can use the --choose-branch and --choose-tag options. These options
prune the graph so that only parents of commits with the choose branch
or tag ids are included in the graph. This gives you more detail
controlled that the git options allowed in the --range command. It
is very useful for determining where branches occurred.

You can choose to keep the git output to re-use multiple times with
different display options or to share by specifying the -k (--keep)
option.
'''
import argparse
import copy
import datetime
import dateutil.parser
import inspect
import os
import re
import subprocess
import sys


VERSION = '0.8.3'
DEFAULT_GITCMD = 'git log --format="|Record:|%h|%p|%d|%ci%n%b"' # --gitcmd
DEFAULT_RANGE = '--all --topo-order'  # --range


class Node:
    r'''
    Each node represents a commit.
    A commit can have zero or parents.
    A parent link is created each time a merge is done.
    '''

    m_list = []
    m_map = {}
    m_list_bydate = []
    m_vars_usage = {}  # nodes that have var values

    def __init__(self, cid, pids=[], branches=[], tags=[], dts=None):
        self.m_cid = cid
        self.m_idx = len(Node.m_list)
        self.m_parents = pids
        self.m_label = ''
        self.m_branches = branches
        self.m_tags = tags
        self.m_children = []

        self.m_vars = {}  # user defined variable values

        self.m_choose = True  # used by the --choose-* options only

        self.m_extra = []
        self.m_dts = dts  # date/time stamp, used for invisible constraints.

        # For squashing.
        self.m_chain_head = None
        self.m_chain_tail = None
        self.m_chain_size = -1

        Node.m_list.append(self)
        Node.m_map[cid] = self

    def is_squashable(self):
        if len(self.m_branches) > 0 or len(self.m_tags) > 0 or len(self.m_parents) > 1 or len(self.m_children) > 1:
            return False
        return True

    def is_squashed(self):
        if self.m_chain_head is None:
            return False
        if self.m_chain_tail is None:
            return False
        return self.m_chain_size > 0 and self.m_cid != self.m_chain_head.m_cid and self.m_cid != self.m_chain_tail.m_cid

    def is_squashed_head(self):
        if self.m_chain_head is None:
            return False
        return self.m_chain_head.m_cid == self.m_cid

    def is_squashed_tail(self):
        if self.m_chain_tail is None:
            return False
        return self.m_chain_tail.m_cid == self.m_cid

    def is_merge_node(self):
        return len(self.m_children) > 1

    def find_chain_head(self):
        if self.is_squashable() == False:
            return None
        if self.m_chain_head is not None:
            return self.m_chain_head

        # Get the head node, traversing via parents.
        chain_head = None
        chain_next = self
        while chain_next is not None and chain_next.is_squashable():
            chain_head = chain_next
            if len(chain_next.m_parents) > 0:
                chain_next = Node.m_map[chain_next.m_parents[0]]
            else:
                chain_next = None
        return chain_head

    def find_chain_tail(self):
        if self.is_squashable() == False:
            return None
        if self.m_chain_tail is not None:
            return self.m_chain_tail

        # Get the tail node, traversing via children.
        chain_tail = None
        chain_next = self
        while chain_next is not None and chain_next.is_squashable():
            chain_tail = chain_next
            if len(chain_next.m_children) > 0:
                chain_next = chain_next.m_children[0]
            else:
                chain_next = None
        return chain_tail

    @staticmethod
    def squash():
        '''
        Squash nodes that in a chain of single commits.
        '''
        update = {}
        for nd in Node.m_list:
            head = nd.find_chain_head()
            if head is not None:
                update[head.m_cid] = head

        for key in update:
            head = update[key]
            tail = head.find_chain_tail()
            cnext = head
            clast = head
            distance = 0
            while clast != tail:
                distance += 1
                clast = cnext
                cnext = cnext.m_children[0]

            cnext = head
            clast = head
            while clast != tail:
                idx = cnext.m_idx
                cid = cnext.m_cid

                Node.m_list[idx].m_chain_head = head
                Node.m_list[idx].m_chain_tail = tail
                Node.m_list[idx].m_chain_size = distance

                Node.m_map[cid].m_chain_head = head
                Node.m_map[cid].m_chain_tail = tail
                Node.m_map[cid].m_chain_size = distance

                clast = cnext
                cnext = cnext.m_children[0]

    def rm_parent(self, pcid):
        while pcid in self.m_parents:
            i = self.m_parents.index(pcid)
            self.m_parents = self.m_parents[:i] + self.m_parents[i+1:]

    def rm_child(self, ccid):
        for i, cnd in reversed(list(enumerate(self.m_children))):
            if cnd.m_cid == ccid:
                self.m_children = self.m_children[:i] + self.m_children[i+1:]


def info(msg, lev=1):
    ''' Print an informational message with the source line number. '''
    print('// INFO:{} {}'.format(inspect.stack()[lev][2], msg))


def infov(opts, msg, lev=1):
    ''' Print an informational message with the source line number. '''
    if opts.verbose > 0:
        print('// INFO:{} {}'.format(inspect.stack()[lev][2], msg))


def warn(msg, lev=1):
    ''' Print a warning  message with the source line number. '''
    print('// WARNING:{} {}'.format(inspect.stack()[lev][2], msg))


def err(msg, lev=1):
    ''' Print an error message and exit. '''
    sys.stderr.write('// ERROR:{} {}\n'.format(inspect.stack()[lev][2], msg))
    sys.exit(1)


def runcmd_long(cmd, show_output=True):
    '''
    Execute a long running shell command with no inputs.
    Capture output and exit status.
    For long running commands, this implementation displays output
    information as it is captured.
    For fast running commands it would be better to use
    subprocess.check_output.
    '''
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    # Read the output 1 character at a time so that it can be
    # displayed in real time.
    output = ''
    while not proc.returncode:
        char = proc.stdout.read(1)
        if not char:
            # all done, wait for returncode to get populated
            break
        else:
            try:
                # There is probably a better way to do this.
                char = char.decode('utf-8')
            except UnicodeDecodeError:
                continue
            output += char
            if show_output:
                sys.stdout.write(char)
                sys.stdout.flush()
    proc.wait()
    return proc.returncode, output


def runcmd_short(cmd, show_output=True):
    '''
    Execute a short running shell command with no inputs.
    Capture output and exit status.
    '''
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        status = 0
    except subprocess.CalledProcessError as obj:
        output = obj.output
        status = obj.returncode

    if show_output:
        sys.stdout.write(output)

    return status, output


def runcmd(cmd, show_output=True):
    '''
    Wrapper for run commands.
    '''
    return runcmd_long(cmd, show_output)


def read(opts):
    '''
    Read the input data.
    The input can come from two general sources: the output of a git
    command or a file that contains the output from a git comment
    (-i).
    '''
    # Run the git command.
    infov(opts, 'reading git repo data')
    out = ''
    if opts.input != '':
        # The user specified a file that contains the input data
        # via the -i option.
        try:
            with open(opts.input, 'r') as ifp:
                out = ifp.read()
        except IOError as e:
            err('input read failed: {}'.format(e))
    else:
        # The user chose to run a git command.
        cmd = opts.gitcmd
        if cmd.replace('%%', '%') == DEFAULT_GITCMD:
            cmd = cmd.replace('%%', '%')
            if opts.cnode_label != '':
                x = cmd.rindex('"')
                cmd = cmd[:x] + '%n{}|{}'.format(opts.cnode_label_recid, opts.cnode_label) + cmd[x:]

            if opts.since != '':
                cmd += ' --since="{}"'.format(opts.since)
            if opts.until != '':
                cmd += ' --until="{}"'.format(opts.until)
            if opts.range != '':
                cmd += ' {}'.format(opts.range)
        else:
            # If the user specified a custom command then we
            # do not allow the user options to affect it.
            if opts.cnode_label != '':
                warn('-l <label> ignored when -g is specified')
            if opts.since != '':
                warn('--since ignored when -g is specified')
            if opts.until != '':
                warn('--until ignored when -g is specified')
            if opts.range != DEFAULT_RANGE:
                warn('--range ignored when -g is specified')

        infov(opts, 'running command: {}'.format(cmd))
        st, out = runcmd(cmd, show_output=opts.verbose > 1)
        if st:
            err('Command failed: {}\n{}'.format(cmd, out))
        infov(opts, 'read {:,} bytes'.format(len(out)))

    if opts.keep is True:
        # The user decided to keep the generated output for
        # re-use.
        ofn = opts.DOT_FILE[0] + '.keep'
        infov(opts, 'writing command output to {}'.format(ofn))
        try:
            with open(ofn, 'w') as ofp:
                ofp.write(out)
        except IOError as e:
            err('unable to write to {}: {}'.format(ofn, e))

    return out.splitlines()


def prune_by_date(opts):
    '''
    Prune by date is --since, --until or --range were specified.
    '''
    if opts.since != '' or opts.until != '' or opts.range != '':
        infov(opts, 'pruning parents')
        nump = 0
        numt = 0
        for i, nd in enumerate(Node.m_list):
            np = []
            for cid in nd.m_parents:
                numt += 1
                if cid in Node.m_map:
                    np.append(cid)
                else:
                    nump += 1
            if len(np) < len(nd.m_parents):  # pruned
                Node.m_list[i].m_parents = np
                Node.m_map[nd.m_cid].m_parents = np
        infov(opts, 'pruned {:,} parent node references out of {:,}'.format(nump, numt))


def prune_by_choice(opts):
    '''
    Prune by --choose-branch and --choose-tag if they were specified.
    '''
    if len(opts.choose_branch) > 0 or len(opts.choose_tag) > 0:
        # The algorithm is as follows:
        #     1. for each branch and tag find the associated node.
        #
        #     2. mark all nodes for deletion (m_choose=False)
        #
        #     3. walk back through graph and tag all nodes accessible
        #        from the parent link as keepers (m_choose=True).
        #        any node found that already has m_choose=True can be
        #        skipped because it was already processed by another
        #        traversal.
        #
        #     4. delete all nodes marked for deletion.
        #        iterate over all nodes, collect the delete ids in a cache
        #        reverse iterate over the cache and remove them
        #        make sure that they are removed from the list and the map
        #        just prior to delete a node, remove it from child list
        #        of its parents and from the parent list of its children.
        #        make sure that all m_idx settings are correctly updated.
        infov(opts, 'pruning graph based on choices')
        bs = {}
        ts = {}

        # initialize
        for b in opts.choose_branch:
            bs[b] = []
        for t in opts.choose_tag:
            ts[t] = []

        for idx in range(len(Node.m_list)):
            Node.m_list[idx].m_choose = False  # step 2

            # Step 1.
            nd =  Node.m_list[idx]
            for b in opts.choose_branch:
                if b in nd.m_branches:
                    bs[b].append(idx)

            for t in opts.choose_tag:
                if t in nd.m_tags:
                    ts[t].append(idx)

        # Warn if any were not found.
        for b, a in sorted(bs.items()):
            if len(a) == 0:
                warn('--choose-branch not found: "{}"'.format(b))
        for t, a in sorted(ts.items()):
            if len(a) == 0:
                warn('--choose-branch not found: "{}"'.format(t))

        # At this point all of the branches and tags have been found.
        def get_parents(idx, parents):
            # Can't use recursion because large graphs may have very
            # long chains.
            # Use a breadth first expansion instead.
            # This works because git commits are always a DAG.
            stack = []
            stack.append(idx)
            while len(stack) > 0:
                idx = stack.pop()
                if idx in parents:
                    continue  # already processed

                nd =  Node.m_list[idx]
                Node.m_list[idx].m_choose = True
                parents[idx] = nd.m_cid
                for pcid in nd.m_parents:
                    pidx = Node.m_map[pcid].m_idx
                    stack.append(pidx)

        parents = {}  # key=idx, val=cid
        for b, a in sorted(bs.items()):
            if len(a) > 0:
                for idx in a:
                    get_parents(idx, parents)
        for t, a in sorted(ts.items()):
            if len(a) > 0:
                for idx in a:
                    get_parents(idx, parents)

        pruning = len(Node.m_list) - len(parents)
        infov(opts, 'keeping {:,}'.format(len(parents)))
        infov(opts, 'pruning {:,}'.format(pruning))
        if pruning == 0:
            warn('nothing to prune')
            return

        # We now have all of the nodes that we want to keep.
        # We need to delete the others.
        todel = []
        for nd in Node.m_list[::-1]:
            if nd.m_choose == False:
                cid = nd.m_cid
                idx = nd.m_idx

                # Update the parents child lists.
                # The parent list is composed of cids.
                # Note that the child lists stored nodes.
                for pcid in nd.m_parents:
                    if pcid in Node.m_map:  # might have been deleted already
                        pnd =  Node.m_map[pcid]
                        if pnd.m_choose == True:  # ignore pruned nodes (e.g. False)
                            pnd.rm_child(cid)

                # Update the child parent lists.
                # The child list is composed of nodes.
                # Note that the parent lists store cids.
                for cnd in nd.m_children:
                    if cnd.m_choose == True:  # ignore pruned nodes (e.g. False)
                        cnd.rm_parent(cid)

                # Actual deletion.
                Node.m_list = Node.m_list[:idx] + Node.m_list[idx+1:]
                del Node.m_map[cid]

        for i, nd in enumerate(Node.m_list):
            Node.m_list[i].m_idx = i
            Node.m_map[nd.m_cid].m_idx = i

        infov(opts, 'remaining {:,}'.format(len(Node.m_list)))


def parse(opts):
    '''
    Parse the node data.
    '''
    infov(opts, 'loading nodes (commit data)')
    nd = None
    lines = read(opts)

    infov(opts, 'parsing read data')
    for line in lines:
        line = line.strip()
        if line.find(u'|Record:|') >= 0:
            flds = line.split('|')
            assert flds[1] == 'Record:'
            cid = flds[2]  # Commit id.
            pids = flds[3].split()  # parent ids
            tags = []
            branches = []
            refs = flds[4].strip()
            try:
                dts = dateutil.parser.parse(flds[5])
            except:
                err('unrecognized date format: {}\n\tline: {}'.format(flds[5], line))
            if len(refs):
                # branches and tags
                if refs[0] == '(' and refs[-1] == ')':
                    refs = refs[1:-1]
                for fld in refs.split(','):
                    fld = fld.strip()
                    if 'tag: ' in fld:
                        tags.append(fld)
                    else:
                        ref = fld
                        if ' -> ' in fld:
                            ref = fld.split(' -> ')[1]
                        branches.append(ref)
            nd = Node(cid, pids, branches, tags, dts)

        if opts.define_var is not None:
            # The user defined one or more variables.
            # Scan each line to see if the variable
            # specification exists.
            for p in opts.define_var:
                var = p[0]
                reg = p[1]
                m = re.search(reg, line)
                if m:
                    # A variable was found.
                    val = m.group(1)

                    # Set the value on the node.
                    idx = nd.m_idx
                    if var not in Node.m_list[idx].m_vars:
                        Node.m_list[idx].m_vars[var] = []
                    Node.m_list[idx].m_vars[var].append(val)

                    # keep track of which nodes have this defined.
                    if var not in Node.m_vars_usage:
                        Node.m_vars_usage[var] = []
                    Node.m_vars_usage[var].append(nd.m_cid)

        if opts.cnode_label_recid in line:
            # Add the additional commit node label data into the node.
            th = opts.cnode_label_maxwidth
            flds = line.split('|')
            idx = nd.m_idx

            def setval(idx, th, val):
                if th > 0:
                    val = val[:th]
                val = val.replace('"', '\\"')
                Node.m_list[idx].m_extra.append(val)

            # Update the field values.
            for fld in flds[1:]: # skip the record field
                # We have the list of fields but these are not, necessarily
                # the same as the variables.
                # Example: @CHID@
                # Example: FOO@CHID@BAR
                # Example: @CHID@ + %s | next field |
                # Get the values for each variable and substitute them.
                found = False
                if opts.define_var is not None:
                    for p in opts.define_var:
                        var = p[0]
                        if var in fld:
                            found = True
                            # The value is defined on this node.
                            # If it isn't we just ignore it.
                            if var in Node.m_list[idx].m_vars:
                                vals = Node.m_list[idx].m_vars[var]
                                if len(vals) == 1:
                                    fld = fld.replace(var, vals[0])
                                    setval(idx, th, fld)
                                else:
                                    # This is hard because there may be
                                    # multiple variables that are vectors
                                    # of different sizes, punt for now.
                                    fld = fld.replace(var, '{}'.format(vals))
                                    setval(idx, th, fld)
                if not found:
                    setval(idx, th, fld)

    if len(Node.m_list) == 0:
        err('no records found')

    prune_by_date(opts)
    prune_by_choice(opts)

    # Update the child list for each node by looking at the parents.
    # This helps us identify merge nodes.
    infov(opts, 'updating children')
    num_edges = 0
    for nd in Node.m_list:
        for p in nd.m_parents:
            num_edges += 1
            Node.m_map[p].m_children.append(nd)

    # Summary of initial read.
    infov(opts, 'found {:,} commit nodes'.format(len(Node.m_list)))
    infov(opts, 'found {:,} commit edges'.format(num_edges))
    if opts.verbose:
        for var in Node.m_vars_usage:
            info('found {:,} nodes with values for variable "{}"'.format(len(Node.m_vars_usage[var]), var))

    # Squash nodes.
    if opts.squash:
        infov(opts, 'squashing chains')
        Node.squash()

    # Create the bydate list to enable ranking using invisible
    # constraints.
    infov(opts, 'sorting by date')
    Node.m_list_bydate = [nd.m_cid for nd in Node.m_list]
    Node.m_list_bydate.sort(key=lambda x: Node.m_map[x].m_dts)


def gendot(opts):
    '''
    Generate a test graph.
    '''
    # Write out the graph stuff.
    infov(opts, 'gendot')

    try:
        ofp = open(opts.DOT_FILE[0], 'w')
    except IOError as e:
        err('file open failed: {}'.format(e))

    # Keep track of the node information so
    # that it can be reported at the end.
    summary = {'num_graph_commit_nodes': 0,
               'num_graph_merge_nodes': 0,
               'num_graph_squash_nodes': 0,
               'total_graph_commit_nodes': 0,  # sum of commit, merge and squash nodes
               'total_commits': 0}   # total nodes with no squashing

    ofp.write('digraph G {\n')
    for v in opts.dot_option:
        if len(opts.font_size) and 'fontsize=' in v:
            v = re.sub(r'(fontsize=)[^,]+,', r'\1"' + opts.font_size + r'",' , v)
        if len(opts.font_name) and 'fontsize=' in v:
            v = re.sub(r'(fontsize=[^,]+),', r'\1, fontname="' + opts.font_name + r'",', v)
        ofp.write('   {}'.format(v))
        if v[-1] != ';':
            ofp.write(';')
        ofp.write('\n')

    ofp.write('\n')
    ofp.write('   // label cnode, mnode and snodes\n')
    for nd in Node.m_list:
        if opts.squash and nd.is_squashed():
            continue
        if nd.is_merge_node():
            label = '\\n'.join(nd.m_extra)
            attrs = opts.mnode.format(label=label)
            ofp.write('   "{}" {};\n'.format(nd.m_cid, attrs))
            summary['num_graph_merge_nodes'] += 1
            summary['total_graph_commit_nodes'] += 1
            summary['total_commits'] += 1
        elif nd.is_squashed_head() or nd.is_squashed_tail():
            label = '\\n'.join(nd.m_extra)
            attrs = opts.snode.format(label=label)
            ofp.write('   "{}" {};\n'.format(nd.m_cid, attrs))
            summary['num_graph_squash_nodes'] += 1
            summary['total_graph_commit_nodes'] += 1
        else:
            label = '\\n'.join(nd.m_extra)
            attrs = opts.cnode.format(label=label)
            ofp.write('   "{}" {};\n'.format(nd.m_cid, attrs))
            summary['num_graph_commit_nodes'] += 1
            summary['total_graph_commit_nodes'] += 1
            summary['total_commits'] += 1

    infov(opts, 'defining edges')
    ofp.write('\n')
    ofp.write('   // edges\n')
    for nd in Node.m_list:
        if nd.is_squashed():
            continue
        elif nd.is_squashed_tail():
            continue

        if nd.is_squashed_head():
            # Special handling for squashed head nodes, create
            # a squash edge between the head and tail.
            attrs = opts.sedge.format(label=nd.m_chain_size)
            ofp.write('   "{}" -> "{}" {};\n'.format(nd.m_cid, nd.m_chain_tail.m_cid, attrs))
            summary['total_commits'] += nd.m_chain_size

        # Create the edges to the parents.
        for pid in nd.m_parents:
            pnd = Node.m_map[pid]
            attrs = ''
            if nd.is_merge_node():
                if len(opts.mnode_pedge) > 0:
                    attrs = opts.mnode_pedge.format(label='{} to {}'.format(nd.m_cid, pid))
                ofp.write('   "{}" -> "{}" {};\n'.format(pid, nd.m_cid, attrs))
            else:
                if len(opts.cnode_pedge) > 0:
                    attrs = opts.cnode_pedge.format(label='{} to {}'.format(nd.m_cid, pid))
                ofp.write('   "{}" -> "{}" {};\n'.format(pid, nd.m_cid, attrs))

    # Annote the tags and branches for each node.
    # Can't use subgraphs because rankdir is not
    # supported.
    infov(opts, 'annotating branches and tags')
    ofp.write('\n')
    ofp.write('   // annotate branches and tags\n')
    first = True
    for idx, nd in enumerate(Node.m_list):
        # technically this is redundant because squashed nodes, by
        # definition, do not have branches or tag refs.
        if nd.is_squashed():
            continue
        if len(nd.m_branches) > 0 or len(nd.m_tags) > 0:
            torank = [nd.m_cid]
            if first:
                first = False
            else:
                ofp.write('\n')

            if len(nd.m_tags) > 0:
                if opts.crunch:
                    # Create the node name.
                    tid = 'tid-{:>08}'.format(idx)
                    label = '\\n'.join(nd.m_tags)
                    attrs = opts.tnode.format(label=label)
                    ofp.write('   "{}" {};\n'.format(tid, attrs))
                    torank += [tid]

                    # Write the connecting edge.
                    ofp.write('   "{}" -> "{}"'.format(tid, nd.m_cid))
                else:
                    torank += nd.m_tags
                    for t in nd.m_tags:
                        # Tag node definitions.
                        attrs = opts.tnode.format(label=t)
                        ofp.write('   "{}+{}" {};\n'.format(nd.m_cid, t, attrs))

                    tl = nd.m_tags
                    ofp.write('   "{}+{}"'.format(nd.m_cid, tl[0]))
                    for t in tl[1:]:
                        ofp.write(' -> "{}+{}"'.format(nd.m_cid, t))
                    ofp.write(' -> "{}"'.format(nd.m_cid))

                attrs = opts.tedge.format(label=nd.m_cid)
                ofp.write(' {};\n'.format(attrs))

            if len(nd.m_branches) > 0:
                if opts.crunch:
                    # Create the node name.
                    bid = 'bid-{:>08}'.format(idx)
                    label = '\\n'.join(nd.m_branches)
                    attrs = opts.bnode.format(label=label)
                    ofp.write('   "{}" {};\n'.format(bid, attrs))
                    torank += [bid]

                    # Write the connecting edge.
                    ofp.write('   "{}" -> "{}"'.format(nd.m_cid, bid))
                else:
                    torank += nd.m_branches
                    for b in nd.m_branches:
                        # Branch node definitions.
                        attrs = opts.bnode.format(label=b)
                        ofp.write('   "{}+{}" {};\n'.format(nd.m_cid, b, attrs))

                    ofp.write('   "{}"'.format(nd.m_cid))
                    for b in nd.m_branches[::-1]:
                        ofp.write(' -> "{}+{}"'.format(nd.m_cid, b))

                attrs = opts.bedge.format(label=nd.m_cid)
                ofp.write(' {};\n'.format(attrs))

            # Make sure that they line up by putting them in the same rank.
            ofp.write('   {{rank=same; "{}"'.format(torank[0]))
            for cid in torank[1:]:
                if opts.crunch:
                    ofp.write('; "{}"'.format(cid))
                else:
                    ofp.write('; "{}+{}"'.format(nd.m_cid, cid))
            ofp.write('};\n')

    # Align nodes by commit date.
    if opts.align_by_date != 'none':
        infov(opts, 'align by {}'.format(opts.align_by_date))
        ofp.write('\n')
        ofp.write('   // rank by date using invisible constraints between groups\n')
        lnd = Node.m_map[Node.m_list_bydate[0]]

        attrs = ['year', 'month', 'day', 'hour', 'minute', 'second']
        for cid in Node.m_list_bydate:
            nd = Node.m_map[cid]
            if nd.is_squashed():
                continue

            for attr in attrs:
                v1 = getattr(nd.m_dts, attr)
                v2 = getattr(lnd.m_dts, attr)
                if v1 < v2:
                    # Add an invisible constraint to guarantee that the
                    # later node appears somewhere to the right.
                    if opts.verbose > 1:
                        info('aligning {} {} to the left of {} {}'.format(lnd.m_cid, lnd.m_dts, nd.m_cid, nd.m_dts))
                    ofp.write('   "{}" -> "{}" [style=invis];\n'.format(lnd.m_cid, nd.m_cid))
                elif v1 > v2:
                    break
                if attr == opts.align_by_date:
                    continue

            if lnd.m_dts < nd.m_dts:
                lnd = nd

    # Output the graph label.
    if opts.graph_label is not None:
        infov(opts, 'generate graph label')
        ofp.write('\n')
        ofp.write('   // graph label\n')
        ofp.write('   {}'.format(opts.graph_label))

        if opts.graph_label[-1] != ';':
            ofp.write(';')
        ofp.write('\n')

    ofp.write('}\n')

    # Output the summary data.
    for k in sorted(summary, key=str.lower):
        v = summary[k]
        ofp.write('// summary:{} {}\n'.format(k, v))
    ofp.close()


def html(opts):
    '''
    Generate an HTML file that allows pan and zoom.
    It uses https://github.com/ariutta/svg-pan-zoom.
    '''
    # TODO: resize the image height on demand
    if opts.html is not None:
        infov(opts, 'generating HTML to {}'.format(opts.html))
        try:
            html = opts.html
            svg = opts.DOT_FILE[0] + '.svg'
            js = 'svg-pan-zoom.min.js'
            with open(html, 'w') as ofp:
                ofp.write('''<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>{4}</title>
    {3}
  </head>
  <body>
    <h3>{4}</h3>
    <div style="border-width:3px; border-style:solid; border-color:lightgrey;">
      <object id="digraph" type="image/svg+xml" data="{0}" style="width:100%; min-height:{2};">
        SVG not supported by this browser.
      </object>
    </div>
    <script>
      window.onload = function() {{
        svgPanZoom('#digraph', {{
          zoomEnabled: true,
          controlIconsEnabled: true,
          fit: true,
          center: true,
          maxZoom: 1000,
          zoomScaleSensitivity: 0.5
        }});
      }};
      window.addEventListener("resize", function() {{
        if (spz != null) {{
          spz.resize();
          spz.fit();
          spz.center();
        }}
      }});
    </script>
  </body>
</html>
'''.format(svg, js, opts.html_min_height, '    \n'.join([x for x in opts.html_head]), opts.html_title))
        except IOError as e:
            err('HTML write failed: {}'.format(e))


def gengraph(opts, fmt):
    '''
    Generate the graph file using dot with -O option.
    '''
    if fmt:
        infov(opts, 'generating {}'.format(fmt))
        cmd = 'dot -T{} -O {}'.format(fmt, opts.DOT_FILE[0])
        if opts.verbose:
            cmd += ' -v'
        infov(opts, 'running command: {}'.format(cmd))
        st, _ = runcmd(cmd, show_output=opts.verbose > 1)
        if st:
            err('command failed with status {}: :"'.format(st, cmd))


def getopts():
    '''
    Get the command line options using argparse.
    '''
    # Trick to capitalize the built-in headers.
    # Unfortunately I can't get rid of the ":" reliably.
    def gettext(s):
        lookup = {
            'usage: ': 'USAGE:',
            'positional arguments': 'POSITIONAL ARGUMENTS',
            'optional arguments': 'OPTIONAL ARGUMENTS',
            'show this help message and exit': 'Show this help message and exit.\n ',
        }
        return lookup.get(s, s)

    argparse._ = gettext  # to capitalize help headers
    base = os.path.basename(sys.argv[0])
    name = os.path.splitext(base)[0]
    usage = '\n  {0} [OPTIONS] <DOT_FILE>'.format(base)
    desc = 'DESCRIPTION:{0}'.format('\n  '.join(__doc__.split('\n')))
    epilog = r'''EXAMPLES:
   # Example 1: help
   $ {0} -h

   # Example 2: generate a dot file
   $ cd <git-repo>
   $ {0} git.dot

   # Example 3: generate a dot file and a PNG file
   #            you can also run dot manually:
   #               $ dot -v -Tpng -O git.dot
   $ cd <git-repo>
   $ {0} --png git.dot

   # Example 4: generate an HTML file that can supports pan and zoom
   #            you will need to copy in svg-pan-zoom.min.js.
   $ cd <git-repo>
   $ {0} --svg --html index.html git.dot
   $ python -m SimpleHTTPServer 8090  # start a simple server
   $ # browse to URL http://localhost:8090/git.html

   # Example 5: add additional data to each commit node and
   #            generate a png file.
   #            it shows the subject, the commit author,
   #            and the commit date (relative).
   $ cd <git-repo>
   $ {0} --png -l '%h|%s|%cn|%cr' git.dot
   $ ls -1 *.png
   git.dot.png

   # Example 6: limit the history commits since 2017-01-01.
   $ {0} --since 2017-01-01 git.dot

   # Example 7: limit the history commits until 2017-01-01.
   $ {0} --until 2017-01-01 git.dot

   # Example 8: force straight edges instead of splines
   $ {0} --dot-option 'splines="false"' git.dot

   # Example 9. generate a caption table
   #            it contains the current date and directory
   #            the background is light yellow
   #            it uses a fixed with font and is left justified.
   $ {0} --png  -L "<<table border=\\"0\\"><tr><td border=\\"1\\" align=\\"left\\" balign=\\"left\\" bgcolor=\\"lightyellow\\"><font face=\\"courier\\" point-size=\\"9\\">Date: $(date)<br/>Dir:  $(pwd)</font></td></tr></table>>" git.dot

   # Example 10. keep the git output for multiple runs
   #             it shows that you can use the original complex setup
   #             (like custom variables) or any subset.
   #             in this case it generates three additional dot files
   #             with different settings.
   $ {0} --png  -D '@CHID@' 'Change-Id: I([0-9a-z]+)' -l '%h|%s|%cn|%cr|@CHID@' --keep git.dot
   $ ls git.dot*
   git.dot      git.dot.keep     git.dot.png
   $ {0} -i git.dot.keep -D '@CHID@' 'Change-Id: I([0-9a-z]+)' -l '%h|%s|%cn|%cr|@CHID@' [label="{{label}}", color="purple"] git01.dot
   $ {0} -i git.dot.keep -l '%h|%s|%cr' [label="{{label}}", color="green"] git02.dot
   $ {0} -i git.dot.keep -l '%h|%s|%cn|%cr' [label="{{label}}", color="magenta"] git03.dot

   # Example 11: only report the commits associated with three branches:
                 origin/1.0.0, origin/1.0.1 and origin/1.1.0
   $ {0} --choose-branch origin/1.0.0 --choose-branch origin/1.0.1 --choose-branch origin/1.1.0 git01.dot

   # Example 11. change the font name and size for the graph, nodes
   #             and edges.
   $ {0} --png --font-name helvetica --font-size 14.0 git.dot

COPYRIGHT:
   Copyright (c) 2017 Joe Linoff, all rights reserved

LICENSE:
   MIT Open Source

PROJECT:
   https://github.com/jlinoff/git2dot
 '''.format(base)
    afc = argparse.RawTextHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=afc,
                                     description=desc[:-2],
                                     usage=usage,
                                     epilog=epilog)

    parser.add_argument('--align-by-date',
                        action='store',
                        choices=['year', 'month', 'day', 'hour', 'minute', 'second', 'none'],
                        default='none',
                        help='''Rank the commits by commit date.
The options allow you to specify the relative positions of nodes with
earlier and later commit dates.  When you specify one of the options
(other than none), the earlier node will always be to the left of the
later node.

   year    Compare years.
   month   Compare years and months.
   day     Compare years, months and days.
   hour    Compare years, months, days and hours.
   minute  Compare years, months, days, hours and minutes.
   second  Compare years, months, days, hours, minutes and seconds.
   none    Do not position by date. Earlier nodes can appear to the
           right of later nodes.

The align operation is different than a rank operation. It merely
guarantees that all nodes later than a node appear to the right of
it. This is done by creating invisible edges.

Be careful when using this option. The invisible edge can cause
nodes to not aligh horizontally which can be a bit jarring.

Default: %(default)s
 ''')

    parser.add_argument('--bedge',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[arrowhead=normal, color="lightblue", dir=none]',
                        help='''Define the bedge attributes.
The bedge is any edge that connects to or from a bnode (see --bnode for details).

Unlike edges that connect cnodes, mnodes and snodes, this is a simple
connection. The parent reference is obvious because of the rank.

Default: %(default)s
 ''')

    parser.add_argument('--bnode',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[label="{label}", color="lightblue", style=filled, shape=box, height=0.15]',
                        help='''Define the bnode attributes.
The bnode is a branch entry for a cnode, mnode or snode. It is only
associated with the node where it was specified as a ref by git.

It always appears at the same rank level as the associated commit node
and normally appears below it.

This node has a different shape by default because it is really an
attribute of a commit node.

See the documentation for --cnode for more attribute details.

Default: %(default)s
 ''')

    parser.add_argument('--choose-branch',
                        action='append',
                        metavar=('BRANCH'),
                        default=[],
                        help='''Choose a branch to include.
By default all branches are included. When you select this option, you
limit the output to commit nodes that are in the branch parent chain.

You can use it to select multiple branches to graph which basically
tells the tool to prune all other branches as endpoints.

This is very useful for comparing commits between related branches.
 ''')

    parser.add_argument('--choose-tag',
                        action='append',
                        metavar=('TAG'),
                        default=[],
                        help='''Choose a tag to include.
By default all tags are included. When you select this option, you
limit the output to commit nodes that are in the tag parent chain.

You can use it to select multiple tags to graph which basically
tells the tool to prune all other tags as endpoints.

This is very useful for comparing commits between related tags.

Make sure that you specify --branch-tag 'tag: TAGNAME' to match
what appears in git.
 ''')

    parser.add_argument('--cnode-pedge',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='',
                        help='''Define the commit node parent edge.
The cnode-pedge is any edge that connects a commit node to its parent.

Empty use the default edge settings.

Default: %(default)s
 ''')

    parser.add_argument('--cnode',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[label="{label}", color="bisque"]',
                        help='''Define the cnode attributes.
The cnode is a commit node which is a git commit that has a single child.

The variable {label} is generated internally. You have complete
control over everything else.

For example, to change the color to green do this:

   --cnode '[label="{label}", shape=ellipse, fontsize=10.0, color="green", style="filled"]

Or to change the shape and fillcolor:

   --cnode '[label="{label}", shape=diamon, fontsize=10.0, color="red", fillcolor="green", style="solid"]

The available attributes are described here: http://www.graphviz.org/doc/info/attrs.html.

Default: %(default)s
 ''')

    parser.add_argument('-c', '--crunch',
                        action='store_true',
                        help='''Crunch branches and tags.
Crunch branches into a single node and tags into a single.
This works around unwieldy placements of the individual
nodes by dot in large graphs.
 ''')

    x = ['graph[rankdir="LR", fontsize=10.0, bgcolor="white"]',
         'node[shape=ellipse, fontsize=10.0, style="filled"]',
         'edge[weight=2, penwidth=1.0, fontsize=10.0, arrowtail="open", dir="back"]']
    parser.add_argument('-d', '--dot-option',
                        action='append',
                        default=x,
                        metavar=('OPTION'),
                        help='''Additional dot options.
For example, to force straight edges add this:

   -d 'splines="false"'

Do not worry about appending a semi-colon. It will be added
automatically.

You can use this to define default top level attributes like
rankdir=LR or the default fontsize to use for all nodes.

Default:
   -d '{}'
 '''.format('\'\n   -d \''.join(x)))

    parser.add_argument('-D', '--define-var',
                        action='append',
                        nargs=2,
                        metavar=('KEY', 'RE'),
                        help='''Define a variable.
Variables are custom data that can be referenced in the commit node
label specification.

This option allows you to extract a value from the commit log
and use it. It is useful for cases where teams have meta-tags
in comments.

Here is an example that shows how to extract change ids of the
form: "Change-Id: I<hex>" and reference it by the name @CHID@.

   -D '@CHID@' 'Change-Id: I([0-9a-z]+)'

You can then reference it like this:

   -l '%s|%ci|@CHID@'

It is best to define the variable as something that is highly unlikely
to occur either in the comments or in the git format specification.

For example, never use % or | or { or } in variable names. Always
surround them with a delimiter like @FOO@.  If you simply specify
@FOO, then this will match @FOO, @FOOBAR and anything else that
contains @FOO which is probably not what you want.
 '''.replace('%', '%%'))

    parser.add_argument('--font-name',
                        action='store',
                        type=str,
                        default='',
                        help='''Change the font name of graph, node and edge objects.
Here is an example: --font-name helvetica.
 ''')

    parser.add_argument('--font-size',
                        action='store',
                        type=str,
                        default='',
                        help='''Change the font size of graph, node and edge objects.
Here is an example: --font-size 14.0.
 ''')

    parser.add_argument('-g', '--gitcmd',
                        action='store',
                        type=str,
                        default=DEFAULT_GITCMD.replace('%', '%%'),
                        help='''Base command for generating the graph data.
If you override this command, make sure that the output syntax is the
same as the default command.

The example below shows a simple gitcmd that sets since:

      -g 'git log --format="|Record:|%h|%p|%d|%ci%n%b" --since 2016-01-01 --all --topo-order'

This is very powerful, you can specify any git command at all to
replace git-log but if you do, remember that you must set up the
correct fields for parsing for everything, including cnode labels.

This option disables the --range, --since and --until options.

Default: %(default)s
 '''.replace('%', '%%'))

    parser.add_argument('--html',
                        action='store',
                        metavar=('FILE'),
                        help='''Generate an HTML file to view the graph.
It uses the svg-pan-zoom JS library to enable panning and zooming.
Please see https://github.com/ariutta/svg-pan-zoom for more details.

The name of the SVG file is DOT_FILE.svg.

The image file reference in the HTML is DOT_FILE.svg.
The svg-pan-zoom script is referenced as svg-pan-zoom.min.js in the HTML.

To use the HTML file you will have to copy the SVG and JS files to
their respective locations or edit the HTML file manually.

You will almost certainly want to update the HTML page title.
 ''')

    x = ['<script src="svg-pan-zoom.min.js"></script>']
    parser.add_argument('--html-head',
                        action='append',
                        metavar=('HTML'),
                        default=x,
                        help='''Insert extra head statements.
Useful for defining script references.

Default:
   '{}'
 '''.format('\'\n   -d \''.join(x)))

    parser.add_argument('--html-min-height',
                        action='store',
                        default='700px',
                        metavar=('MIN-HEIGHT'),
                        help='''Set the minimum height for the graph.
Long skinny graphs can be a real problem when zooming so setting
this 700px or greater really helps.

Default: %(default)s
 ''')

    parser.add_argument('--html-title',
                        action='store',
                        default='git2dot',
                        metavar=('STRING'),
                        help='''Set the HTML page title.
Default: %(default)s
 ''')

    parser.add_argument('-i', '--input',
                        action='store',
                        metavar=('FILE'),
                        default='',
                        help='''Input data.
You can use this to avoid running git commands.
It is useful for testing.
 ''')

    parser.add_argument('-k', '--keep',
                        action='store_true',
                        help='''Keep the git command output for re-use.
This is great for trying out different display options or for
sharing.

The kept output file name is DOT_FILE.keep.
 ''')

    parser.add_argument('-l', '--cnode-label',
                        action='store',
                        metavar=('LABEL_SPEC'),
                        #default='%h'.replace('%', '%%'),
                        default='%h',
                        help='''Define the label used to identify cnodes, mnodes and snodes in the
graph.

Lines are separated by "|"'s. The contents of a line can be a git
format specification like %s or a variable defined by -D like @CHID@
or simply text.

Here is an example that defines the first line as the abbrieviated
commit hash, the second line as the commit subject, the third line as
the date is ISO-8601 format and the fourth line as the @CHID@ value:

   -l '%h|%s|%ci|@CHID@'

If you specify -l '', there will be no labels which is not very
useful.

You can specify the maximum width of a line using -w.

Default: %(default)s
 '''.replace('%', '%%'))

    parser.add_argument('-L', '--graph-label',
                        action='store',
                        metavar=('DOT_LABEL'),
                        help='''Define a graph label.
This is a convenience option that could be also be speficied as -d
'graph=[label="..."]'. It is used to define labels for the graph.

The labels can be quite complex. The following example shows how
to build a label that is actually an HTML-like table.

   -L "<<table border=\\"0\\"><tr><td border=\\"1\\" align=\\"left\\" balign=\\"left\\" bgcolor=\\"lightyellow\\"><font face=\\"courier\\" point-size=\\"9\\">Date: $(date)<br/>Dir:  $(pwd)</font></td></tr></table>>"

The result is a left justified, fixed font output with a small border
that displays the date and directory that the graph was created in.
 ''')

    parser.add_argument('--mnode-pedge',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='',
                        help='''Define the merge node parent edge.
The mnode-pedgeis any edge that connects a merge node to its parent.

Empty use the default edge settings.

Default: %(default)s
 ''')

    parser.add_argument('--mnode',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[label="{label}", color="lightpink"]',
                        help='''Define the mnode attributes.
The mnode is a commit node which is a commit that has more than one
child. It can only be created by a git merge operation.

See the documentation for --cnode for more attribute details.

Default: %(default)s
 ''')

    parser.add_argument('--png',
                        action='store_true',
                        help='''Use dot to generate a PNG file.
This option is only valid if -o is specified.
It is the same as running "dot -Tpng -O DOT_FILE".
 ''')

    parser.add_argument('--range',
                        action='store',
                        metavar=('GIT-RANGE'),
                        default=DEFAULT_RANGE,
                        help='''Only consider git commits that fall within the range.
These are command line arguments used for defining the range.
By default use all commits in the range.

You can add any git log command line options that you want.

For example, you could specify

   --range "--since 2016-01-01"

instead of

   --since 2016-01-01.

This option is ignored if -g is specified.

Default: %(default)s
 ''')

    parser.add_argument('-s', '--squash',
                        action='store_true',
                        help='''Squash sequences of simple commits into a single commit.
The default is not to squash.
 ''')

    parser.add_argument('--since',
                        action='store',
                        metavar=('DATE'),
                        default='',
                        help='''Only consider git commits since the specified date.
This is the same as the --since option to git log.
The default is since the first commit.
This option is ignored if -g is specified.
 ''')

    parser.add_argument('--sedge',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[label="{label}", style=dotted, arrowhead="none", dir="none"]',
                        help='''Define the sedge attributes.
The sedge is any edge that connects the head and tail squashed nodes
(see --snode for details).

Typically this is a dotted line with a count of the number of nodes
that were squashed.

Default: %(default)s
 ''')

    parser.add_argument('--snode',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[label="{label}", color="tomato"]',
                        help='''Define the snode attributes.
The snode defines the head and tail nodes of a squashed node sequence.

See the documentation for --cnode for more attribute details.

See the documentation for -s for squash details.
 ''')

    parser.add_argument('--svg',
                        action='store_true',
                        help='''Use dot to generate a SVG file.
This option is only valid if -o is specified.
It is the same as running "dot -Tsvg -O DOT_FILE".

Default: %(default)s
 ''')

    parser.add_argument('--tedge',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[arrowhead=normal, color="thistle", dir=none]',
                        help='''Define the tedge attributes.
The tedge is any edge that connects to or from a tnode (see --tnode for details).

Unlike edges that connect cnodes, mnodes and snodes, this is a simple
connection. The parent reference is obvious because of the rank.

Default: %(default)s
 ''')

    parser.add_argument('--tnode',
                        action='store',
                        metavar=('DOT_ATTR_LIST'),
                        default='[label="{label}", color="thistle", style=filled, shape=box, height=0.15]',
                        help='''Define the tnode attributes.
The tnode is a tag entry for a cnode, mnode or snode. It is only
associated with the node where it was specified as a ref by git.

It always appears at the same rank level as the associated commit node
and normally appears above it.

This node has a different shape by default because it is really an
attribute of a commit node.

See the documentation for --cnode for more attribute details.

Default: %(default)s
 ''')

    parser.add_argument('--until',
                        action='store',
                        metavar=('DATE'),
                        default='',
                        help='''Only consider git commits until the specified date.
This is the same as the --until option to git log.
The default is until the last commit.
This option is ignored if -g is specified.
 ''')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='''Increase the level of verbosity.
-v    shows the basic steps
-v -v shows a lot of output for debugging
 ''')

    parser.add_argument('-V', '--version',
                        action='version',
                        version='%(prog)s version {0}'.format(VERSION),
                        help="""Show program's version number and exit.
 """)

    parser.add_argument('-w', '--cnode-label-maxwidth',
                        action='store',
                        type=int,
                        metavar=('WIDTH'),
                        default=32,
                        help='''Maximum width of a line for a cnode label.
See -l for more details.
 ''')

    parser.add_argument('-x', '--cnode-label-recid',
                        action='store',
                        metavar=('STRING'),
                        default='@@@git2dot-label@@@:',
                        help='''Record identifier for cnode-label fields.
When -l is specified, an extra set of format data is appended to the
gitcmd (-g). This data must be uniquely identified so this option is
used to define the record. It must not appear as random text in a git
comment so it must be odd.

Default: %(default)s
''')

    # Positional arguments at the end.
    parser.add_argument('DOT_FILE',
                        nargs=1,
                        help='''Graphviz dot file name.
If the .dot extension is not specified, it is appended
automatically.
''')

    opts = parser.parse_args()
    return opts


def cmdline(opts):
    '''
    Re-generate the command line as a string.
    '''
    if opts.verbose:
        cli = []
        qs = [' ', '\t', '|', '?', '$', '#']  # tokens that will trigger a quote
        for arg in sys.argv:
            arg = arg.replace('\\', '\\\\').replace('"', '\\"')
            q = False
            for q in qs:
                if q in arg:
                    arg = '"' + arg + '"'
                    break
            cli.append(arg)
        cmd = ' '.join(cli)
        infov(opts, 'cmdline = {}'.format(cmd))


def main():
    '''
    main
    '''
    try:
        # Make everything unicode in python 2.7.
        reload(sys)
        sys.setdefaultencoding('utf8')
    except NameError:
        pass

    opts = getopts()
    cmdline(opts)
    parse(opts)
    gendot(opts)
    html(opts)
    if opts.png:
        gengraph(opts, 'png')
    if opts.svg:
        gengraph(opts, 'svg')
    infov(opts, 'done')


if __name__ == '__main__':
    main()
