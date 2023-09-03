@Library(value="Jenkins_Jenlib@nextrelease.v0.7.8",changelog=false)

// just harded project_laoyt part
// can be reduced to one file version/project_laoyt.yml
def project_layout = [
    fs_kws_config_path: "_infra/jenlib_lib/cicd/package.deliver.pipe.cfg.yml",
    fs_agent_env_settings_yml: "version/recipe-jenlib/agent_env_settings.yml"
]

def kws = [params:[:], project_layout: project_layout]

jen_flow(
    agent_env_settings_yaml: project_layout.fs_agent_env_settings_yml,
    kws_config_file: project_layout.fs_kws_config_path,
    kws: kws
){
    stage('prepare') {
        sh "ls ${kws.const.subpath}"
        echo "USER `whoami`\nUID  `id -u`\nGID  `id -g`"
        updateGitlabCommitStatus name: 'build', state: 'pending'
    }

    stage('resolve-deps') {
        sh "ls ${kws.const.subpath}"
        echo "USER `whoami`\nUID  `id -u`\nGID  `id -g`"
        sshagent(['sys_objx_ssh']) {
            dir(kws.const.subpath){
                sh 'task -t tasks/ci.tasks.yml resolve-deps WDIR=$(realpath .)'
            }
        }
        updateGitlabCommitStatus name: 'build', state: 'pending'
    }

    catchError { dir(kws.const.subpath) {
        jen.step_stages_from_tasks(
            kws,
            kws.const.subpath,
            kws.params.taskfile,
            kws.params.ci_task
        )

        stage('build-docs') {
            sh 'task mkdocs:build'
        }

        stage('publish') {
            def git_info_config = readYaml file: 'version/git_info_config.yml'
            def git_info_json = readJSON file: '__build_info/mxpack/git_info.json'

            sh 'task ci:publish-flow'
        }
    }}


    stage('report') {dir(kws.const.subpath) {
        if (kws.const.jenkins_artifacts_paths){
            archiveArtifacts artifacts: kws.const.jenkins_artifacts_paths, fingerprint: false
        } else {
            jinEchoMark("No jenkins_artifacts_paths Configured")
        }
        if (kws.const.junit_artifacts_path){
            junit testResults: kws.const.junit_artifacts_path, allowEmptyResults: true
        } else {
            jinEchoMark("No junit_artifacts_path Configured")
        }

        sh "task ci:report"
    }}

    stage('notify') {
        updateGitlabCommitStatus name: 'build', state: 'success'
        // email_result(kws.params.notify_users)
    }

    stage('cleanup') {
        dir(kws.const.subpath){
            sh 'task ci:cleanup:hard'
        }
    }
}
