// @Library(value="Jenkins_Shared_Lib@1.1.x",changelog=false)
@Library(value="Jenkins_Jenlib@master",changelog=false)

// ===== /SHARED PART ====
// --- globas vars ---
def kw = [
    consts: [
        build_type: 'jobs:create',
        patterns: ['_infra/mxpack_lib/cicd/jobs_def/*.groovy'],
        repo: "objx/mxpack"
    ],
    jnode_label: 'mx_conda_java_dw',
    // ---/ sys
    scmvars: null,
    cmds: [],
    tstages: [:],
    prj_dir: '.',
    commits: []
    // ---\ sys

]

node(kw.jnode_label) { timestamps {

    stage('fetch') {
        echo 'Fetch source'
        def scmvars = checkout scm
        jen.set_build_name(currentBuild, scmvars, kw.consts.build_type)
        kw['scmvars'] = scmvars
        jen.desc_from_commits(currentBuild, kw)
    }

    stage('prepare'){
        echo "cleanup: rm -rf _out"
        sh "rm -rf _out"
    }
    stage('create:jobs:local'){
        echo "@info: action.jobdsl=create:jobs:local target.repo=${kw.consts.repo} target.file.pattern='${kw.consts.patterns}'"
        jobDsl targets: kw.consts.patterns.join('\n'),
            lookupStrategy: 'SEED_JOB',
            removedJobAction: 'DELETE',
            removedViewAction: 'DELETE'
    }
    stage('update:gitlab:webhooks'){
        sh 'echo curl gilab:/project'
    }
}}
