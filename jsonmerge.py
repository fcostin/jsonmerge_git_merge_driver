"""
example of custom merge driver for files that contain JSON-encoded objects.

Not-supported

*   merging inside git stash
*   merging inside git rebase
*   merging files that are not JSON files
*   octopus merges

Two limited merge strategies are supported:

1.  if the source and destination files are equal when interpreted as JSON objects,
    merge them as that JSON value, written to file in a normalised format.

2.  if the source and destimation files are not equal when interpreted as JSON objects,
    check that the source, destination and base JSON values are all JSON objects
    with the same top-level keys. If they are, compute a shallow merge using top-level
    key value pairs:
    *   compute a top-level attribute patch between the base JSON value and the source JSON value
    *   apply the top-level attribute patch to the destination JSON value
    The result is deemed the merged JSON value.
    Write the merged JSON value to file in a normalised format.

Note that there are many scenarios not covered by 1 and 2. In this case this
merge tool gives up and returns nonzero, which puts git into the merge conflict state.

Note also that the automatic merge policy in case 1 and case 2 may not do what you want.

If case 1 does not do what you want, you are likely doing something rather questionable.

It is plausible that case 2 might not do what you want in some cases: it regards the
patch from base to source as having higher priority than the patch from base to
destination, and resolves conflicts according to priority. This might not make sense for you.

References:

1.  How to wire a custom merge driver in to git
    https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver

2.  What values you can pass in to the merge driver on the command line
    https://github.com/git/git/blob/f1d4a28250629ae469fc5dd59ab843cb2fd68e12/ll-merge.c

3.  Simple example of the plumbing to wire in a merge driver, with a trivial dumb driver script
    https://github.com/Praqma/git-merge-driver

4.  Undocumented ways to discover what branches are involved from inside the
    merge driver context (does not work reliably in all situations -- e.g. stashing, rebase)
    https://stackoverflow.com/questions/24302644/how-to-retrieve-branch-names-in-a-custom-git-merge-driver

5.  Workflows for merging XML/JSON game content data
    http://bitsquid.blogspot.com/2010/06/avoiding-content-locks-and-conflicts-3.html
"""

import json
import os
import subprocess
import sys



def discover_source_branch():
    # warning: not guaranteed to always work
    # there is no GITHEAD_* env var defined if we're invoked because of git stash
    prefix = 'GITHEAD_'
    for k in os.environ:
        if k.startswith(prefix):
            branch = os.environ[k]
            sha = k[len(prefix):]
            return (branch, sha)
    return None


def discover_destination_branch():
    result = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], capture_output=True)
    assert result.returncode == 0
    branch_name = result.stdout.decode('utf-8').strip()
    result = subprocess.run(["git", "rev-parse", branch_name], capture_output=True)
    assert result.returncode == 0
    sha = result.stdout.decode('utf-8').strip()
    return (branch_name, sha)


def unique(values):
    return len(set(values)) == 1


def objects_have_common_schema(values):
    # same type?
    types = set(map(type, values))
    if not unique(types):
        return False
    # type is object?
    t = types.pop()
    if t != type({}):
        return False
    # keys are all the same?
    return unique(map(frozenset, values))


def compute_patch(old, new):
    p = {}
    assert set(old) == set(new)
    for k in old:
        if new[k] != old[k]:
            p[k] = new[k]
    return p


def apply_patch(old, p):
    assert set(p) <= set(old)
    new = {}
    for k in old:
        if k in p:
            new[k] = p[k]
        else:
            new[k] = old[k]
    return new


def main():
    """
	# driver = jsonmerge.py %P %O %A %B

        /*
		 * merge.<name>.driver specifies the command line:
		 *
		 *	command-line
		 *
		 * The command-line will be interpolated with the following
		 * tokens and is given to the shell:
		 *
		 *    %O - temporary file name for the merge base.
		 *    %A - temporary file name for our version.
		 *    %B - temporary file name for the other branches' version.
		 *    %L - conflict marker length
		 *    %P - the original path (safely quoted for the shell)
		 *
		 * The external merge driver should write the results in the
		 * file named by %A, and signal that it has done with zero exit
		 * status.
		 */

    Ref: https://github.com/git/git/blob/5f9953d2c365bffed6f9ee0c6966556bd4d7e2f4/ll-merge.c#L270-L287

    """

    context = {
        'original_path': sys.argv[1],
        'base_tempfile': sys.argv[2],
        'destination_tempfile': sys.argv[3], # our version is the destination branch
        'source_tempfile': sys.argv[4], # other version, the branch being merged into our branch
        'source_branch': discover_source_branch(),
        'destination_branch': discover_destination_branch(),
    }

    with open(context['base_tempfile'], 'r') as f:
        base_value = json.load(f)

    with open(context['source_tempfile'], 'r') as f:
        source_value = json.load(f)

    with open(context['destination_tempfile'], 'r') as f:
        destination_value = json.load(f)

    merged_value = None
    # is source equal to destination (value equality?)
    if source_value == destination_value:
        # if so, merge is trivial
        merged_value = source_value
    elif objects_have_common_schema((base_value, destination_value, source_value)):
        # Let p(b, d) denote patch from base to destination
        # Let p(b, s) denote patch from base to source
        # Policy: (will give bad results in general): let us regard the change in source as higher priority.
        # Evaluate merge as: apply(apply(b, p(b, d)), p(b, s)) = apply(d, p(b, s))

        p_b_s = compute_patch(base_value, source_value)
        merged_value = apply_patch(destination_value, p_b_s)

        print('jsonmerge of source json value into destination json value with respect to common base json value')
        print('n.b. path: %s' % (context['original_path'], ))
        print('')
        print('base_value: %r' % (base_value, ))
        print('destination_value: %r' % (destination_value, ))
        print('source_value: %r' % (source_value, ))
        print('')
        print('patch from base to source: %r' % (p_b_s, ))
        print('')
        print('merged value: %r' % (merged_value, ))

    else:
        # leave confict unresolved if we aren't merging json object values with a common "schema"
        pass


    if merged_value is not None:
        with open(context['destination_tempfile'], 'w+') as f:
            json.dump(merged_value, f, sort_keys=True, indent=4)
        return 0
    return -1


if __name__ == '__main__':
    sys.exit(main())
