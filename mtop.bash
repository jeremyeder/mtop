_kubectl_ld_completions()
{
    local cur prev opts crs
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="list get check logs delete config help"

    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
        return 0
    fi

    if [[ "$prev" =~ ^(get|check|logs|delete)$ ]]; then
        crs=$(ls ./mocks/crs 2>/dev/null | sed 's/\.json$//' | sed "s/_/\//g")
        COMPREPLY=( $(compgen -W "${crs}" -- "${cur}") )
        return 0
    fi
}

complete -F _kubectl_ld_completions ./kubectl-ld

_kubectl_ld()
{
  local cur prev words cword
  _init_completion || return

  case "${prev}" in
    simulate)
      COMPREPLY=( $(compgen -W "canary bluegreen rolling shadow" -- "$cur") )
      return 0
      ;;
  esac
}
complete -F _kubectl_ld kubectl-ld
